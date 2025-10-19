/**
 * RaceAnimator
 * Main orchestrator for F1 telemetry animation
 * Coordinates telemetry loading, interpolation, rendering, and playback
 */

class RaceAnimator {
    constructor(canvasId) {
        // Canvas setup
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            throw new Error(`Canvas element with id "${canvasId}" not found`);
        }

        this.ctx = this.canvas.getContext('2d');
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;

        // Core modules
        this.telemetryLoader = new TelemetryLoader();
        this.trackRenderer = new TrackRenderer(this.ctx, this.canvas.width, this.canvas.height);
        this.driverAnimator = new DriverAnimator(this.ctx, this.trackRenderer);
        this.playbackController = null;  // Initialized after loading data
        this.uiManager = new UIManager();

        // Animation state
        this.isInitialized = false;
        this.lastFrameTime = performance.now();
        this.animationFrameId = null;

        // Handle window resize
        window.addEventListener('resize', () => this._onWindowResize());
    }

    /**
     * Initialize the animation system
     * Sets up event listeners and prepares for data loading
     */
    initialize() {
        this.uiManager.setupControlListeners({
            play: () => this._play(),
            pause: () => this._pause(),
            rewind: () => this._rewind(),
            speedChange: (speed) => this._setSpeed(speed),
            seekChange: (progress) => this._seek(progress)
        });

        this.isInitialized = true;
        this.uiManager.showInfo('F1 Race Animator initialized. Ready to load telemetry data.');
    }

    /**
     * Load telemetry data from JSON structure
     * @param {Object} telemetryData - Telemetry data in expected format
     */
    async loadTelemetryData(telemetryData) {
        if (!this.isInitialized) {
            this.uiManager.showError('Animator not initialized');
            return false;
        }

        try {
            // Load and validate telemetry
            if (!this.telemetryLoader.loadFromJSON(telemetryData)) {
                this.uiManager.showError('Failed to load telemetry data');
                return false;
            }

            const drivers = this.telemetryLoader.getDrivers();
            if (drivers.length === 0) {
                this.uiManager.showError('No drivers found in telemetry data');
                return false;
            }

            // Initialize playback controller with time range
            const timeRange = this.telemetryLoader.getTimeRange();
            this.playbackController = new PlaybackController(timeRange);

            // Initialize driver animator
            this.driverAnimator.initializeDrivers(drivers);

            // Update UI
            let totalDataPoints = 0;
            drivers.forEach(driver => {
                const count = this.telemetryLoader.getTelemetryPointCount(driver.id);
                totalDataPoints += count;
            });
            this.uiManager.updateStats(drivers.length, totalDataPoints);

            // Load track: Always use session key from F1_TRACKS database (SVG-accurate track)
            const sessionKey = telemetryData.sessionKey || telemetryData.session_key;
            if (sessionKey) {
                this.trackRenderer.loadTrackBySessionKey(sessionKey);
            } else if (telemetryData.track && Array.isArray(telemetryData.track)) {
                // Fallback: Use custom track data if provided
                this.trackRenderer.loadTrackFromData(telemetryData.track);
            }
            // Note: No longer generating fallback tracks - always use defined track layouts

            // Force reset animation state to show new track immediately
            this.driverAnimator.reset();

            // Initialize all drivers to their starting positions
            for (const driver of drivers) {
                const telemetry = this.telemetryLoader.getDriverTelemetry(driver.id);
                if (telemetry && telemetry.length > 0) {
                    // Set driver to first position
                    this.driverAnimator.updateDriver(driver.id, telemetry[0]);
                }
            }

            this._render();

            // Load final race results from backend
            if (sessionKey) {
                try {
                    const resultsResponse = await fetch(`http://localhost:8001/api/race-results/${sessionKey}`);
                    if (resultsResponse.ok) {
                        const data = await resultsResponse.json();
                        const finalResults = data.results || data.drivers || [];
                        if (finalResults.length > 0) {
                            this.driverAnimator.setFinalResults(finalResults);
                            // Display final results immediately
                            this.uiManager.displayFinalResults(finalResults);
                            this.uiManager.showInfo(`Loaded final race results: ${finalResults.length} drivers finished`);
                        }
                    }
                } catch (error) {
                    console.error('Failed to load final race results:', error);
                }
            }

            this.uiManager.showInfo(`Loaded ${drivers.length} drivers with ${totalDataPoints} data points`);
            return true;
        } catch (error) {
            this.uiManager.showError(`Error loading telemetry: ${error.message}`);
            return false;
        }
    }

    /**
     * Start animation loop
     */
    start() {
        if (!this.playbackController) {
            this.uiManager.showError('No telemetry data loaded');
            return;
        }

        this._animate();
    }

    /**
     * Main animation loop
     * Called via requestAnimationFrame for smooth 60 FPS rendering
     * @private
     */
    _animate() {
        const now = performance.now();
        const deltaTime = now - this.lastFrameTime;
        this.lastFrameTime = now;

        // Update playback timing
        const shouldContinue = this.playbackController.update();

        // Update all drivers' positions for current time
        const currentTime = this.playbackController.getCurrentTime();
        const drivers = this.telemetryLoader.getDrivers();

        for (const driver of drivers) {
            const telemetry = this.telemetryLoader.getDriverTelemetry(driver.id);
            if (!telemetry || telemetry.length === 0) continue;

            // Get interpolated position at current time
            const position = Interpolator.getPositionAtTime(telemetry, currentTime);
            if (position) {
                this.driverAnimator.updateDriver(driver.id, position);
            }
        }

        // Render frame
        this._render();

        // Update UI
        this._updateUI(deltaTime);

        // Continue animation loop if not at end
        if (shouldContinue) {
            this.animationFrameId = requestAnimationFrame(() => this._animate());
        } else {
            this.playbackController.pause();
            this.uiManager.updatePlayState(false);
        }
    }

    /**
     * Render current frame to canvas
     * @private
     */
    _render() {
        // Clear canvas and draw track
        this.trackRenderer.renderTrack();

        // Draw DRS zones (disabled)
        // this.trackRenderer.drawDRSZones();

        // Render all drivers
        this.driverAnimator.renderAllDrivers();
    }

    /**
     * Update UI elements each frame
     * @private
     */
    _updateUI(deltaTime) {
        // Update time display
        this.uiManager.updateTimeDisplay(this.playbackController.getTimeDisplay());

        // Update progress
        this.uiManager.updateProgress(this.playbackController.getProgress());

        // Update FPS
        const fps = this.uiManager.calculateFPS(deltaTime);
        this.uiManager.updateFPS(fps);

        // Update driver list - use live standings that change with race progress
        const standings = this.driverAnimator.getDriverStandings();
        const maxLaps = this.telemetryLoader.getMaxLap();
        this.uiManager.updateDriverList(standings, this.driverAnimator, maxLaps);

        // Update play state indication
        this.uiManager.updatePlayState(this.playbackController.isCurrentlyPlaying());
    }

    /**
     * Handle play button
     * @private
     */
    _play() {
        if (!this.playbackController) return;

        if (!this.playbackController.isCurrentlyPlaying()) {
            this.playbackController.play();
            this._animate();
        }
    }

    /**
     * Handle pause button
     * @private
     */
    _pause() {
        if (!this.playbackController) return;
        this.playbackController.pause();
    }

    /**
     * Handle rewind button
     * @private
     */
    _rewind() {
        if (!this.playbackController) return;

        this.playbackController.rewind();
        this.driverAnimator.reset();

        // Render frame at start
        this._render();
        this._updateUI(0);
    }

    /**
     * Handle speed change
     * @private
     */
    _setSpeed(speed) {
        if (!this.playbackController) return;
        this.playbackController.setSpeed(speed);
        this.uiManager.updateSpeed(speed);
    }

    /**
     * Handle seek/progress change
     * @private
     */
    _seek(progress) {
        if (!this.playbackController) return;

        // Convert progress percentage to actual time
        const duration = this.playbackController.getTotalDuration();
        const timeRange = this.telemetryLoader.getTimeRange();
        const targetTime = timeRange.start + (progress / 100) * duration;

        this.playbackController.seekTo(targetTime);
        this.driverAnimator.reset();

        // Render frame at seek position
        this._render();
        this._updateUI(0);
    }

    /**
     * Handle window resize
     * @private
     */
    _onWindowResize() {
        if (!this.canvas) return;

        // Update canvas size
        this.canvas.width = this.canvas.offsetWidth;
        this.canvas.height = this.canvas.offsetHeight;

        // Reinitialize track renderer with new dimensions
        if (this.trackRenderer) {
            this.trackRenderer = new TrackRenderer(this.ctx, this.canvas.width, this.canvas.height);
        }

        // Redraw current frame
        this._render();
    }

    /**
     * Generate a track path from telemetry data bounds
     * @private
     * @param {Array} drivers - Array of driver objects
     * @returns {Array} Track path points
     */
    _generateTrackFromTelemetry(drivers) {
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;

        // Find bounds from all telemetry points
        for (const driver of drivers) {
            const telemetry = this.telemetryLoader.getDriverTelemetry(driver.id);
            if (!telemetry) continue;

            for (const point of telemetry) {
                minX = Math.min(minX, point.x);
                maxX = Math.max(maxX, point.x);
                minY = Math.min(minY, point.y);
                maxY = Math.max(maxY, point.y);
            }
        }

        // If no valid bounds found, return empty
        if (minX === Infinity || maxX === -Infinity || minY === Infinity || maxY === -Infinity) {
            return [];
        }

        // Generate a track outline with padding
        const padding = (maxX - minX) * 0.15;
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;
        const radiusX = (maxX - minX) / 2 + padding;
        const radiusY = (maxY - minY) / 2 + padding;

        // Create an elliptical track path
        const trackPath = [];
        const segments = 64;
        for (let i = 0; i < segments; i++) {
            const angle = (i / segments) * Math.PI * 2;
            const x = centerX + Math.cos(angle) * radiusX;
            const y = centerY + Math.sin(angle) * radiusY;
            trackPath.push({ x, y });
        }

        return trackPath;
    }

    /**
     * Get current animation state for debugging
     * @returns {Object} Current state information
     */
    getState() {
        return {
            isPlaying: this.playbackController?.isCurrentlyPlaying() || false,
            currentTime: this.playbackController?.getCurrentTime() || 0,
            duration: this.playbackController?.getTotalDuration() || 0,
            drivers: this.telemetryLoader.getDrivers().length,
            progress: this.playbackController?.getProgress() || 0,
            speed: this.playbackController?.getSpeed() || 1.0
        };
    }
}
