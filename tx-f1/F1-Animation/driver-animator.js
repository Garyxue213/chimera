/**
 * DriverAnimator
 * Handles rendering and animation of individual F1 drivers on the track
 * Draws driver positions, indicators (speed, gear, throttle, brake), and driver trails
 */

class DriverAnimator {
    constructor(canvasContext, trackRenderer) {
        this.ctx = canvasContext;
        this.trackRenderer = trackRenderer;
        this.drivers = new Map();        // Map<driverId, DriverState>
        this.trailLength = 100;          // Number of previous positions to draw
    }

    /**
     * Brighten dark colors for better visibility on dark background
     * @private
     */
    _brightenColor(hexColor) {
        // Parse hex color
        let hex = hexColor.replace('#', '');
        let r = parseInt(hex.substr(0, 2), 16);
        let g = parseInt(hex.substr(2, 2), 16);
        let b = parseInt(hex.substr(4, 2), 16);

        // If color is dark (sum < 255), brighten it
        const brightness = r + g + b;
        if (brightness < 255) {
            // Increase brightness by multiplying each channel
            const factor = 255 / brightness * 0.8; // Don't go to pure white
            r = Math.min(255, Math.round(r * factor));
            g = Math.min(255, Math.round(g * factor));
            b = Math.min(255, Math.round(b * factor));
        }

        return `rgb(${r}, ${g}, ${b})`;
    }

    /**
     * Initialize driver rendering state
     * @param {Array} drivers - Array of driver objects with id, name, number, code, team, color
     */
    initializeDrivers(drivers) {
        drivers.forEach(driver => {
            this.drivers.set(driver.id, {
                id: driver.id,
                name: driver.name,
                number: driver.number,
                code: driver.code || String(driver.number),  // 3-letter driver code (e.g. "HAM")
                team: driver.team,
                color: driver.color,
                currentPosition: { x: 0, y: 0 },
                previousPositions: [],  // Trail history
                telemetry: {
                    speed: 0,
                    gear: 0,
                    throttle: 0,
                    brake: 0,
                    drs: false,
                    lapNumber: 0
                },
                lapNumber: 0,  // Current lap number for standings
                telemetryIndex: 0  // Track position in telemetry array
            });
        });
    }

    /**
     * Update a driver's position and telemetry for the current frame
     * @param {string} driverId - Driver identifier
     * @param {Object} telemetryData - Interpolated telemetry {x, y, speed, gear, throttle, brake, drs, lapNumber}
     */
    updateDriver(driverId, telemetryData) {
        if (!this.drivers.has(driverId)) return;

        const driver = this.drivers.get(driverId);

        // Use in_pit flag from telemetry data
        driver.isInPitBox = telemetryData.in_pit === true;

        // Update position
        const newPos = this.trackRenderer.worldToCanvas(telemetryData.x, telemetryData.y);

        // Maintain trail history
        driver.previousPositions.push(newPos);
        if (driver.previousPositions.length > this.trailLength) {
            driver.previousPositions.shift();
        }

        driver.currentPosition = newPos;

        // Track lap number from telemetry for standings calculation
        driver.lapNumber = telemetryData.lapNumber || 0;

        // Update telemetry
        driver.telemetry = {
            speed: Math.round(telemetryData.speed),
            gear: telemetryData.gear,
            throttle: telemetryData.throttle,
            brake: telemetryData.brake,
            drs: telemetryData.drs,
            lapNumber: telemetryData.lapNumber
        };
    }

    /**
     * Render all drivers on canvas
     */
    renderAllDrivers() {
        for (const driver of this.drivers.values()) {
            this._drawDriverTrail(driver);
            this._drawDriver(driver);
            this._drawDriverLabel(driver);
            this._drawTelemetryIndicators(driver);
        }
    }

    /**
     * Draw driver trail (previous positions)
     * @private
     */
    _drawDriverTrail(driver) {
        if (driver.previousPositions.length < 2) return;

        // Draw fading trail
        this.ctx.strokeStyle = driver.color;
        this.ctx.lineWidth = 2;
        this.ctx.globalAlpha = 0.3;

        this.ctx.beginPath();
        this.ctx.moveTo(driver.previousPositions[0].x, driver.previousPositions[0].y);

        for (let i = 1; i < driver.previousPositions.length; i++) {
            const pos = driver.previousPositions[i];
            this.ctx.lineTo(pos.x, pos.y);
        }

        this.ctx.stroke();
        this.ctx.globalAlpha = 1.0;
    }

    /**
     * Draw driver position as circle with team color
     * @private
     */
    _drawDriver(driver) {
        const radius = 8;

        // If driver is in pit box, draw pit box instead
        if (driver.isInPitBox) {
            // Pit box rectangle
            this.ctx.fillStyle = 'rgba(255, 100, 0, 0.3)';
            this.ctx.fillRect(
                driver.currentPosition.x - 15,
                driver.currentPosition.y - 10,
                30,
                20
            );

            // Pit box border
            this.ctx.strokeStyle = '#ff6400';
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(
                driver.currentPosition.x - 15,
                driver.currentPosition.y - 10,
                30,
                20
            );

            // Driver car in pit box (smaller circle) with brightened color
            this.ctx.fillStyle = this._brightenColor(driver.color);
            this.ctx.beginPath();
            this.ctx.arc(driver.currentPosition.x, driver.currentPosition.y, 5, 0, Math.PI * 2);
            this.ctx.fill();

            return;
        }

        // Normal track rendering
        // Draw driver circle (main) with brightened color for visibility
        this.ctx.fillStyle = this._brightenColor(driver.color);
        this.ctx.beginPath();
        this.ctx.arc(driver.currentPosition.x, driver.currentPosition.y, radius, 0, Math.PI * 2);
        this.ctx.fill();

        // Draw outer ring for visibility
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(driver.currentPosition.x, driver.currentPosition.y, radius + 2, 0, Math.PI * 2);
        this.ctx.stroke();

        // Draw DRS indicator if active (red glow)
        if (driver.telemetry.drs) {
            this.ctx.strokeStyle = 'rgba(255, 0, 0, 0.8)';
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.arc(driver.currentPosition.x, driver.currentPosition.y, radius + 4, 0, Math.PI * 2);
            this.ctx.stroke();
        }
    }

    /**
     * Draw driver code and name label above position
     * @private
     */
    _drawDriverLabel(driver) {
        const x = driver.currentPosition.x;
        const y = driver.currentPosition.y - 25;

        // Driver code background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(x - 18, y - 10, 36, 20);

        // Driver code text (3-letter acronym like "HAM")
        this.ctx.fillStyle = '#fff';
        this.ctx.font = 'bold 12px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(driver.code, x, y);
    }

    /**
     * Draw telemetry indicators (speed, gear, throttle, brake) next to driver
     * @private
     */
    _drawTelemetryIndicators(driver) {
        const x = driver.currentPosition.x + 20;
        const y = driver.currentPosition.y;
        const lineHeight = 12;
        const maxWidth = 60;

        // Semi-transparent background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
        this.ctx.fillRect(x - 5, y - 35, maxWidth, 70);

        // Speed indicator
        this._drawIndicator(x, y - 30, 'S', `${driver.telemetry.speed}`, '#00ff00');

        // Gear indicator
        this._drawIndicator(x, y - 18, 'G', `${driver.telemetry.gear}`, '#00d4ff');

        // Throttle bar (green)
        this._drawBar(x, y - 6, driver.telemetry.throttle, '#00ff00', 'T');

        // Brake bar (red)
        this._drawBar(x, y + 6, driver.telemetry.brake, '#ff0000', 'B');
    }

    /**
     * Draw a telemetry indicator (speed, gear, etc.)
     * @private
     */
    _drawIndicator(x, y, label, value, color) {
        this.ctx.font = 'bold 10px Courier New';
        this.ctx.fillStyle = color;
        this.ctx.textAlign = 'left';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(`${label}:${value}`, x, y);
    }

    /**
     * Draw a throttle/brake bar indicator
     * @private
     */
    _drawBar(x, y, value, color, label) {
        const barWidth = 50;
        const barHeight = 4;

        // Background bar (dark)
        this.ctx.fillStyle = 'rgba(100, 100, 100, 0.5)';
        this.ctx.fillRect(x, y - barHeight / 2, barWidth, barHeight);

        // Filled bar (based on value 0-1)
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y - barHeight / 2, barWidth * Math.max(0, Math.min(1, value)), barHeight);

        // Label
        this.ctx.font = 'bold 9px Courier New';
        this.ctx.fillStyle = '#999';
        this.ctx.textAlign = 'right';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(label, x - 3, y);
    }

    /**
     * Get current telemetry for a specific driver
     * @param {string} driverId - Driver identifier
     * @returns {Object} Current telemetry state or null
     */
    getDriverTelemetry(driverId) {
        const driver = this.drivers.get(driverId);
        return driver ? driver.telemetry : null;
    }

    /**
     * Get driver position
     * @param {string} driverId - Driver identifier
     * @returns {Object} {x, y} in canvas coordinates or null
     */
    getDriverPosition(driverId) {
        const driver = this.drivers.get(driverId);
        return driver ? { ...driver.currentPosition } : null;
    }

    /**
     * Get all drivers' current positions for position calculation
     * @returns {Array} Array of {driverId, position: {x, y}}
     */
    getAllDriverPositions() {
        const positions = [];
        for (const [id, driver] of this.drivers.entries()) {
            positions.push({
                driverId: id,
                name: driver.name,
                position: { ...driver.currentPosition }
            });
        }
        return positions;
    }

    /**
     * Calculate driver standings based on lap progress and position
     * Primary sort: lap number (higher = ahead), Secondary sort: lap progress
     * @returns {Array} Sorted array of {driverId, name, code, position, lapNumber}
     */
    getDriverStandings() {
        const standings = [];

        for (const driver of this.drivers.values()) {
            // Use lap number + relative position on current lap for accurate standings
            // Lap number is primary, track progress (x position) is secondary
            standings.push({
                driverId: driver.id,
                name: driver.name,
                number: driver.number,
                code: driver.code,
                team: driver.team,
                color: driver.color,
                lapNumber: driver.lapNumber,
                trackProgress: driver.currentPosition.x  // Progress within current lap
            });
        }

        // Sort: first by lap (descending = more laps ahead), then by track progress within lap
        standings.sort((a, b) => {
            // Primary: higher lap number is ahead
            if (b.lapNumber !== a.lapNumber) {
                return b.lapNumber - a.lapNumber;
            }
            // Secondary: within same lap, further along track (higher x) is ahead
            return b.trackProgress - a.trackProgress;
        });

        return standings.map((standing, index) => ({
            ...standing,
            position: index + 1
        }));
    }

    /**
     * Set final race results (from backend calculated results)
     * @param {Array} results - Array of final results from backend
     */
    setFinalResults(results) {
        this.finalResults = results || [];
    }

    /**
     * Get final race results
     * @returns {Array} Final race results or empty if not set
     */
    getFinalResults() {
        return this.finalResults || [];
    }

    /**
     * Reset all driver animation state
     */
    reset() {
        for (const driver of this.drivers.values()) {
            driver.previousPositions = [];
            driver.currentPosition = { x: 0, y: 0 };
        }
    }
}
