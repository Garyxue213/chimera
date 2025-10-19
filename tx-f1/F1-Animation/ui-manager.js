/**
 * UIManager
 * Manages UI updates including driver list, controls, and real-time statistics
 * Synchronizes DOM elements with animation state
 */

class UIManager {
    constructor() {
        // Cache DOM elements for performance
        this.elements = {
            playBtn: document.getElementById('playBtn'),
            pauseBtn: document.getElementById('pauseBtn'),
            rewindBtn: document.getElementById('rewindBtn'),
            speedSlider: document.getElementById('speedSlider'),
            speedValue: document.getElementById('speedValue'),
            progressSlider: document.getElementById('progressSlider'),
            progressValue: document.getElementById('progressValue'),
            timeDisplay: document.getElementById('timeDisplay'),
            driverCount: document.getElementById('driverCount'),
            dataPoints: document.getElementById('dataPoints'),
            driversList: document.getElementById('driversList'),
            fpsCounter: document.getElementById('fpsCounter')
        };

        // Ensure all elements exist
        this._validateElements();

        // FPS tracking
        this.fpsHistory = [];
        this.lastFpsUpdate = performance.now();
    }

    /**
     * Validate that all required DOM elements exist
     * @private
     */
    _validateElements() {
        for (const [key, element] of Object.entries(this.elements)) {
            if (!element) {
                console.warn(`UI element not found: ${key}`);
            }
        }
    }

    /**
     * Update time display (MM:SS / MM:SS)
     * @param {string} timeString - Formatted time string
     */
    updateTimeDisplay(timeString) {
        if (this.elements.timeDisplay) {
            this.elements.timeDisplay.textContent = timeString;
        }
    }

    /**
     * Update progress bar
     * @param {number} progress - Progress percentage (0-100)
     */
    updateProgress(progress) {
        if (this.elements.progressSlider) {
            this.elements.progressSlider.value = progress;
        }
        if (this.elements.progressValue) {
            this.elements.progressValue.textContent = `${Math.round(progress)}%`;
        }
    }

    /**
     * Update speed display
     * @param {number} speed - Speed multiplier
     */
    updateSpeed(speed) {
        if (this.elements.speedSlider) {
            this.elements.speedSlider.value = speed;
        }
        if (this.elements.speedValue) {
            this.elements.speedValue.textContent = `${speed.toFixed(2)}x`;
        }
    }

    /**
     * Update driver list with current telemetry
     * @param {Array} standings - Array of driver standings with position and telemetry
     * @param {DriverAnimator} driverAnimator - Reference to driver animator for telemetry
     * @param {number} maxLaps - Maximum laps in the session (for progress bar)
     */
    updateDriverList(standings, driverAnimator, maxLaps = 56) {
        if (!this.elements.driversList) return;

        this.elements.driversList.innerHTML = '';

        standings.forEach((standing, index) => {
            const telemetry = driverAnimator.getDriverTelemetry(standing.driverId);
            if (!telemetry) return;

            const driverCard = document.createElement('div');
            driverCard.className = 'driver-card';
            driverCard.style.borderLeftColor = standing.color || '#00d4ff';
            driverCard.style.borderLeftWidth = '4px';

            // Position indicator (P1, P2, etc.)
            const positionColor = this._getPositionColor(standing.position);

            driverCard.innerHTML = `
                <div class="driver-name" style="color: ${standing.color || '#00d4ff'}">
                    P${standing.position}: ${standing.code} - ${standing.name}
                </div>
                <div class="driver-stat">
                    <span class="stat-label">Speed:</span>
                    <span class="stat-value">${telemetry.speed} km/h</span>
                </div>
                <div class="driver-stat">
                    <span class="stat-label">Gear:</span>
                    <span class="stat-value">${telemetry.gear}</span>
                </div>
                <div class="driver-stat">
                    <span class="stat-label">Throttle:</span>
                    <span class="stat-value">${Math.round(telemetry.throttle * 100)}%</span>
                </div>
                <div class="driver-stat">
                    <span class="stat-label">Brake:</span>
                    <span class="stat-value">${Math.round(telemetry.brake * 100)}%</span>
                </div>
                <div class="driver-stat">
                    <span class="stat-label">Lap Progress:</span>
                    <span class="stat-value">${telemetry.lapNumber}/${maxLaps}</span>
                </div>
                <div style="background: rgba(0,0,0,0.3); border-radius: 3px; height: 4px; margin: 3px 0; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #00d4ff, #00ff88); height: 100%; width: ${(telemetry.lapNumber / maxLaps) * 100}%;"></div>
                </div>
                ${telemetry.drs ? '<div class="driver-stat" style="color: #ff3333;"><span>🚀 DRS Active</span></div>' : ''}
            `;

            this.elements.driversList.appendChild(driverCard);
        });
    }

    /**
     * Display final race results (static podium)
     * @param {Array} finalResults - Array of final race results with position and driver info
     */
    displayFinalResults(finalResults) {
        if (!this.elements.driversList) return;

        this.elements.driversList.innerHTML = '';

        finalResults.forEach((result) => {
            const driverCard = document.createElement('div');
            driverCard.className = 'driver-card';
            driverCard.style.borderLeftColor = result.color || '#00d4ff';
            driverCard.style.borderLeftWidth = '4px';

            // Get position-specific styling
            const positionColor = this._getPositionColor(result.position);

            driverCard.innerHTML = `
                <div class="driver-name" style="color: ${result.color || '#00d4ff'}">
                    P${result.position}: ${result.code} - ${result.name}
                </div>
                <div class="driver-stat">
                    <span class="stat-label">Final Lap:</span>
                    <span class="stat-value">${result.final_lap || result.lapNumber || 0}</span>
                </div>
                <div class="driver-stat">
                    <span class="stat-label">Final Position:</span>
                    <span class="stat-value">${result.final_position ? `(${result.final_position.toFixed(1)})` : 'N/A'}</span>
                </div>
                <div class="driver-stat">
                    <span class="stat-label">Session:</span>
                    <span class="stat-value">${result.session_key || 'N/A'}</span>
                </div>
            `;

            this.elements.driversList.appendChild(driverCard);
        });
    }

    /**
     * Get position-based color
     * @private
     */
    _getPositionColor(position) {
        switch (position) {
            case 1: return '#FFD700'; // Gold for 1st
            case 2: return '#C0C0C0'; // Silver for 2nd
            case 3: return '#CD7F32'; // Bronze for 3rd
            default: return '#00d4ff';
        }
    }

    /**
     * Update session statistics
     * @param {number} driverCount - Number of active drivers
     * @param {number} dataPoints - Total data points loaded
     */
    updateStats(driverCount, dataPoints) {
        if (this.elements.driverCount) {
            this.elements.driverCount.textContent = driverCount;
        }
        if (this.elements.dataPoints) {
            this.elements.dataPoints.textContent = dataPoints;
        }
    }

    /**
     * Update FPS counter
     * @param {number} fps - Current frames per second
     */
    updateFPS(fps) {
        if (this.elements.fpsCounter) {
            this.elements.fpsCounter.textContent = `FPS: ${Math.round(fps)}`;
        }
    }

    /**
     * Calculate FPS from frame timing
     * Should be called once per animation frame
     * @param {number} deltaTime - Time since last frame in milliseconds
     * @returns {number} Average FPS over recent frames
     */
    calculateFPS(deltaTime) {
        const fps = 1000 / Math.max(deltaTime, 1);

        // Keep history of last 30 frames
        this.fpsHistory.push(fps);
        if (this.fpsHistory.length > 30) {
            this.fpsHistory.shift();
        }

        // Return average
        return this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length;
    }

    /**
     * Set up event listeners for controls
     * @param {Object} callbacks - Object with play, pause, rewind, speedChange, seekChange callbacks
     */
    setupControlListeners(callbacks) {
        if (this.elements.playBtn && callbacks.play) {
            this.elements.playBtn.addEventListener('click', callbacks.play);
        }

        if (this.elements.pauseBtn && callbacks.pause) {
            this.elements.pauseBtn.addEventListener('click', callbacks.pause);
        }

        if (this.elements.rewindBtn && callbacks.rewind) {
            this.elements.rewindBtn.addEventListener('click', callbacks.rewind);
        }

        if (this.elements.speedSlider && callbacks.speedChange) {
            this.elements.speedSlider.addEventListener('input', (e) => {
                callbacks.speedChange(parseFloat(e.target.value));
            });
        }

        if (this.elements.progressSlider && callbacks.seekChange) {
            this.elements.progressSlider.addEventListener('change', (e) => {
                callbacks.seekChange(parseFloat(e.target.value));
            });
        }
    }

    /**
     * Enable or disable controls
     * @param {boolean} enabled - True to enable controls
     */
    setControlsEnabled(enabled) {
        const controls = [
            this.elements.playBtn,
            this.elements.pauseBtn,
            this.elements.rewindBtn,
            this.elements.speedSlider,
            this.elements.progressSlider
        ];

        controls.forEach(control => {
            if (control) {
                control.disabled = !enabled;
            }
        });
    }

    /**
     * Update play/pause button state
     * @param {boolean} isPlaying - True if animation is playing
     */
    updatePlayState(isPlaying) {
        if (this.elements.playBtn) {
            this.elements.playBtn.style.opacity = isPlaying ? '0.5' : '1.0';
        }
        if (this.elements.pauseBtn) {
            this.elements.pauseBtn.style.opacity = isPlaying ? '1.0' : '0.5';
        }
    }

    /**
     * Show error message to user
     * @param {string} message - Error message
     */
    showError(message) {
        console.error(message);
        alert(`Animation Error: ${message}`);
    }

    /**
     * Show info message
     * @param {string} message - Info message
     */
    showInfo(message) {
        console.log(message);
    }

    /**
     * Clear all UI elements
     */
    clear() {
        if (this.elements.driversList) {
            this.elements.driversList.innerHTML = '';
        }
        this.updateTimeDisplay('00:00 / 00:00');
        this.updateProgress(0);
        this.updateSpeed(1.0);
        this.updateStats(0, 0);
    }
}
