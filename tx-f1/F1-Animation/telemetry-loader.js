/**
 * TelemetryLoader
 * Handles loading, parsing, and organizing telemetry data from FastF1/OpenF1 APIs
 * or imported JSON data structures
 */

class TelemetryLoader {
    constructor() {
        this.drivers = new Map();        // Map<driverId, DriverData>
        this.sessions = new Map();       // Map<sessionId, SessionData>
        this.timeRange = { start: 0, end: 0 };
    }

    /**
     * Load telemetry data from JSON structure
     * Expected format:
     * {
     *   drivers: {
     *     'driver1': { name, number, team, telemetry: [...] },
     *     ...
     *   }
     * }
     */
    loadFromJSON(data) {
        this.drivers.clear();

        if (!data.drivers) {
            console.error('Invalid data format: missing drivers object');
            return false;
        }

        let minTime = Infinity;
        let maxTime = -Infinity;

        // Process each driver's telemetry
        for (const [driverId, driverData] of Object.entries(data.drivers)) {
            if (!driverData.telemetry || !Array.isArray(driverData.telemetry)) {
                console.warn(`Skipping driver ${driverId}: no telemetry data`);
                continue;
            }

            // Validate and normalize telemetry points
            const normalizedTelemetry = this._normalizeTelemetry(driverData.telemetry);

            if (normalizedTelemetry.length === 0) {
                console.warn(`Skipping driver ${driverId}: no valid telemetry points`);
                continue;
            }

            // Track time range across all drivers
            minTime = Math.min(minTime, normalizedTelemetry[0].time);
            maxTime = Math.max(maxTime, normalizedTelemetry[normalizedTelemetry.length - 1].time);

            // Store driver data
            this.drivers.set(driverId, {
                id: driverId,
                name: driverData.name || `Driver ${driverId}`,
                number: driverData.number || parseInt(driverId),
                code: driverData.code || driverData.name_acronym || String(driverData.number || driverId).substring(0, 3),  // 3-letter driver code
                team: driverData.team || 'Unknown',
                color: driverData.color || this._generateColor(driverId),
                telemetry: normalizedTelemetry
            });
        }

        // Set time range for synchronization
        if (minTime !== Infinity && maxTime !== -Infinity) {
            this.timeRange = { start: minTime, end: maxTime };
        }

        return this.drivers.size > 0;
    }

    /**
     * Normalize telemetry data points
     * Ensures all points have required fields and proper types
     */
    _normalizeTelemetry(telemetryArray) {
        return telemetryArray
            .map(point => ({
                time: parseFloat(point.time) || 0,
                x: parseFloat(point.x) || 0,
                y: parseFloat(point.y) || 0,
                speed: parseFloat(point.speed) || 0,
                gear: parseInt(point.gear) || 0,
                throttle: Math.max(0, Math.min(1, parseFloat(point.throttle) || 0)),
                brake: Math.max(0, Math.min(1, parseFloat(point.brake) || 0)),
                drs: Boolean(point.drs),
                lapNumber: parseInt(point.lapNumber) || 0
            }))
            .filter(point => !isNaN(point.time) && !isNaN(point.x) && !isNaN(point.y))
            .sort((a, b) => a.time - b.time);
    }

    /**
     * Generate a consistent, distinct color for each driver
     * Uses driver ID for reproducible colors
     */
    _generateColor(driverId) {
        // Use driver ID as seed for color generation
        const seed = driverId.charCodeAt(0) + (driverId.length * 17);
        const hue = (seed * 137.508) % 360;
        const saturation = 70 + (seed % 20);
        const lightness = 45 + (seed % 20);
        return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    }

    /**
     * Get all drivers
     */
    getDrivers() {
        return Array.from(this.drivers.values());
    }

    /**
     * Get specific driver data
     */
    getDriver(driverId) {
        return this.drivers.get(driverId);
    }

    /**
     * Get time range of telemetry data
     */
    getTimeRange() {
        return { ...this.timeRange };
    }

    /**
     * Convert time value to formatted string (MM:SS)
     */
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }

    /**
     * Get total duration in seconds
     */
    getTotalDuration() {
        return this.timeRange.end - this.timeRange.start;
    }

    /**
     * Get telemetry point at specific index for a driver
     */
    getTelemetryPoint(driverId, index) {
        const driver = this.drivers.get(driverId);
        if (!driver || !driver.telemetry) return null;
        return driver.telemetry[index] || null;
    }

    /**
     * Get number of telemetry points for a driver
     */
    getTelemetryPointCount(driverId) {
        const driver = this.drivers.get(driverId);
        return driver?.telemetry?.length || 0;
    }

    /**
     * Get all telemetry for a driver
     */
    getDriverTelemetry(driverId) {
        const driver = this.drivers.get(driverId);
        return driver?.telemetry || [];
    }

    /**
     * Get maximum lap number across all drivers' telemetry
     * Returns the highest lapNumber found in any driver's data
     */
    getMaxLap() {
        let maxLap = 0;
        for (const driver of this.drivers.values()) {
            if (!driver.telemetry) continue;
            for (const point of driver.telemetry) {
                if (point.lapNumber && point.lapNumber > maxLap) {
                    maxLap = point.lapNumber;
                }
            }
        }
        return maxLap || 56;  // Default to 56 if no lap data found
    }
}
