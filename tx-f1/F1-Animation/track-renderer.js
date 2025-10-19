/**
 * TrackRenderer
 * Handles rendering of the F1 track layout on HTML5 canvas
 */

class TrackRenderer {
    constructor(canvasContext, width, height) {
        this.ctx = canvasContext;
        this.width = width;
        this.height = height;
        this.currentSessionKey = null;
        this.trackData = null;
        this.trackPath = this._generateTrackPath();
        this.pitLane = null;
        this.scale = { x: 1, y: 1 };
        this.offset = { x: 0, y: 0 };
        // Austin track bounds (from backend coordinate space)
        this.coordinateBounds = {
            minX: -3000,
            maxX: 2500,
            minY: -2500,
            maxY: 2000
        };
        this._calculateTrackBounds();
    }

    /**
     * Set the track based on session key
     */
    loadTrackBySessionKey(sessionKey) {
        this.currentSessionKey = sessionKey;

        // Get track data from global F1_TRACKS if available
        if (typeof getTrackLayout === 'function') {
            this.trackData = getTrackLayout(sessionKey);
            if (this.trackData) {
                this.trackPath = this.trackData.trackPath;
                this.pitLane = this.trackData.pitLane || null;
                this._calculateTrackBounds();
                return true;
            }
        }

        // Fallback to default track
        this.trackPath = this._generateTrackPath();
        this._calculateTrackBounds();
        return false;
    }

    /**
     * Generate a sample track path for visualization
     * In production, this would be replaced with actual track coordinates
     */
    _generateTrackPath() {
        // Austin Circuit of The Americas simplified track path (fallback)
        return [
            { x: 100, y: 100 }, { x: 150, y: 90 }, { x: 180, y: 110 },
            { x: 190, y: 155 }, { x: 160, y: 190 }, { x: 100, y: 200 },
            { x: 50, y: 170 }, { x: 50, y: 110 }, { x: 100, y: 100 }
        ];
    }

    /**
     * Calculate bounding box of track and set scaling
     */
    _calculateTrackBounds() {
        // Use minimal zoom for true world space representation
        // 0.05 pixels per world unit = zoomed out view (2x further than 0.1)
        const pixelsPerUnit = 0.05;
        this.scale.x = pixelsPerUnit;
        this.scale.y = pixelsPerUnit;

        // Pan to show a viewport of the world
        // Center on the track area
        const minX = this.coordinateBounds.minX;
        const maxX = this.coordinateBounds.maxX;
        const minY = this.coordinateBounds.minY;
        const maxY = this.coordinateBounds.maxY;

        // Calculate center of world space
        const centerWorldX = (minX + maxX) / 2;
        const centerWorldY = (minY + maxY) / 2;

        // Pan to center the world on canvas (shifted left by 180px, up by 200px)
        this.offset.x = this.width / 2 - centerWorldX * pixelsPerUnit - 180;
        this.offset.y = this.height / 2 - centerWorldY * pixelsPerUnit - 200;
    }

    /**
     * Transform track coordinates to canvas coordinates
     */
    worldToCanvas(x, y) {
        return {
            x: x * this.scale.x + this.offset.x,
            y: y * this.scale.y + this.offset.y
        };
    }

    /**
     * Render the track on canvas
     */
    renderTrack() {
        // Clear canvas
        this.ctx.fillStyle = '#0a0e27';
        this.ctx.fillRect(0, 0, this.width, this.height);

        // Draw grid background
        this._drawGrid();

        // Draw pit lane (disabled)
        // if (this.pitLane) {
        //     this._drawPitLane();
        // }

        // Draw track centerline (disabled - inaccurate)
        // this._drawTrackLine();

        // Draw track boundaries (disabled - inaccurate)
        // this._drawTrackBoundaries();
    }

    /**
     * Draw pit lane area
     * @private
     */
    _drawPitLane() {
        if (!this.pitLane) return;

        const topLeft = this.worldToCanvas(this.pitLane.x - this.pitLane.width / 2, this.pitLane.y - this.pitLane.length / 2);
        const width = this.pitLane.width * this.scale.x;
        const height = this.pitLane.length * this.scale.y;

        // Pit lane background (dark gray with transparency)
        this.ctx.fillStyle = 'rgba(50, 50, 70, 0.3)';
        this.ctx.fillRect(topLeft.x, topLeft.y, width, height);

        // Pit lane border
        this.ctx.strokeStyle = '#ffaa00';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(topLeft.x, topLeft.y, width, height);

        // Pit lane label
        this.ctx.fillStyle = '#ffaa00';
        this.ctx.font = 'bold 12px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText('PIT', topLeft.x + width / 2, topLeft.y + height / 2);
    }

    /**
     * Draw background grid for reference
     */
    _drawGrid() {
        const gridSize = 50;
        this.ctx.strokeStyle = 'rgba(0, 212, 255, 0.05)';
        this.ctx.lineWidth = 0.5;

        for (let x = 0; x < this.width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.height);
            this.ctx.stroke();
        }

        for (let y = 0; y < this.height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.width, y);
            this.ctx.stroke();
        }
    }

    /**
     * Draw main track line
     */
    _drawTrackLine() {
        if (this.trackPath.length === 0) return;

        this.ctx.strokeStyle = '#00d4ff';
        this.ctx.lineWidth = 8;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        this.ctx.beginPath();
        const firstPoint = this.worldToCanvas(this.trackPath[0].x, this.trackPath[0].y);
        this.ctx.moveTo(firstPoint.x, firstPoint.y);

        for (let i = 1; i < this.trackPath.length; i++) {
            const point = this.worldToCanvas(this.trackPath[i].x, this.trackPath[i].y);
            this.ctx.lineTo(point.x, point.y);
        }

        // Close the loop
        this.ctx.closePath();
        this.ctx.stroke();
    }

    /**
     * Draw track boundaries (kerbs)
     */
    _drawTrackBoundaries() {
        if (this.trackPath.length === 0) return;

        const kerb = 6; // Kerb width

        // Inner boundary (red kerb)
        this.ctx.strokeStyle = '#ff3333';
        this.ctx.lineWidth = 4;
        this._drawOffsetPath(this.trackPath, -kerb);

        // Outer boundary (yellow/orange)
        this.ctx.strokeStyle = '#ff9900';
        this.ctx.lineWidth = 4;
        this._drawOffsetPath(this.trackPath, kerb);
    }

    /**
     * Draw an offset path (parallel to main track)
     */
    _drawOffsetPath(basePath, offset) {
        if (basePath.length < 2) return;

        const offsetPath = [];

        for (let i = 0; i < basePath.length; i++) {
            const prev = basePath[(i - 1 + basePath.length) % basePath.length];
            const current = basePath[i];
            const next = basePath[(i + 1) % basePath.length];

            const v1 = { x: current.x - prev.x, y: current.y - prev.y };
            const v2 = { x: next.x - current.x, y: next.y - current.y };

            const len1 = Math.sqrt(v1.x * v1.x + v1.y * v1.y) || 1;
            const len2 = Math.sqrt(v2.x * v2.x + v2.y * v2.y) || 1;

            const dir1 = { x: -v1.y / len1, y: v1.x / len1 };
            const dir2 = { x: -v2.y / len2, y: v2.x / len2 };

            const avgDir = {
                x: (dir1.x + dir2.x) / 2,
                y: (dir1.y + dir2.y) / 2
            };

            const avgLen = Math.sqrt(avgDir.x * avgDir.x + avgDir.y * avgDir.y) || 1;
            offsetPath.push({
                x: current.x + (avgDir.x / avgLen) * offset,
                y: current.y + (avgDir.y / avgLen) * offset
            });
        }

        this.ctx.beginPath();
        const firstPoint = this.worldToCanvas(offsetPath[0].x, offsetPath[0].y);
        this.ctx.moveTo(firstPoint.x, firstPoint.y);

        for (let i = 1; i < offsetPath.length; i++) {
            const point = this.worldToCanvas(offsetPath[i].x, offsetPath[i].y);
            this.ctx.lineTo(point.x, point.y);
        }

        this.ctx.closePath();
        this.ctx.stroke();
    }

    /**
     * Draw DRS zones
     */
    drawDRSZones() {
        // DRS zones would be defined by specific track sections
        this.ctx.fillStyle = 'rgba(255, 100, 100, 0.1)';

        // Example DRS zone
        const zone = [
            { x: 200, y: 100 },
            { x: 250, y: 90 },
            { x: 280, y: 110 },
            { x: 230, y: 120 }
        ];

        this.ctx.beginPath();
        const firstPoint = this.worldToCanvas(zone[0].x, zone[0].y);
        this.ctx.moveTo(firstPoint.x, firstPoint.y);

        for (let i = 1; i < zone.length; i++) {
            const point = this.worldToCanvas(zone[i].x, zone[i].y);
            this.ctx.lineTo(point.x, point.y);
        }

        this.ctx.closePath();
        this.ctx.fill();
    }

    /**
     * Load track from external API or data source
     */
    loadTrackFromData(trackData) {
        if (trackData && Array.isArray(trackData)) {
            this.trackPath = trackData;
            this._calculateTrackBounds();
        }
    }

    /**
     * Get canvas dimensions
     */
    getCanvasDimensions() {
        return { width: this.width, height: this.height };
    }

    /**
     * Get track bounds in world coordinates
     */
    getTrackBounds() {
        let minX = Infinity, maxX = -Infinity;
        let minY = Infinity, maxY = -Infinity;

        for (const point of this.trackPath) {
            minX = Math.min(minX, point.x);
            maxX = Math.max(maxX, point.x);
            minY = Math.min(minY, point.y);
            maxY = Math.max(maxY, point.y);
        }

        return { minX, maxX, minY, maxY };
    }
}
