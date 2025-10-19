/**
 * ElevenLabs Text-to-Speech Service
 * Handles narration of F1 lap analysis using ElevenLabs API
 */

class ElevenLabsService {
  constructor(apiKey = null) {
    this.apiKey = apiKey || import.meta.env.VITE_ELEVENLABS_API_KEY;
    this.voiceId = 'JBFqnCBsd6RMkjVY3vHJ'; // Default voice (Rachel)
    this.baseUrl = 'https://api.elevenlabs.io/v1';
    this.audioCache = new Map();
  }

  /**
   * Generate speech from text
   * @param {string} text - Text to convert to speech
   * @param {Object} options - Configuration options
   * @returns {Promise<Blob>} Audio blob
   */
  async synthesizeText(text, options = {}) {
    if (!this.apiKey) {
      console.warn('ElevenLabs API key not configured');
      return null;
    }

    // Check cache first
    const cacheKey = `${text}_${options.voiceId || this.voiceId}`;
    if (this.audioCache.has(cacheKey)) {
      return this.audioCache.get(cacheKey);
    }

    try {
      const voiceId = options.voiceId || this.voiceId;
      const response = await fetch(
        `${this.baseUrl}/text-to-speech/${voiceId}`,
        {
          method: 'POST',
          headers: {
            'Accept': 'audio/mpeg',
            'xi-api-key': this.apiKey,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: text,
            model_id: 'eleven_monolingual_v1',
            voice_settings: {
              stability: 0.5,
              similarity_boost: 0.75,
            },
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`ElevenLabs API error: ${response.statusText}`);
      }

      const audioBlob = await response.blob();

      // Cache the result
      this.audioCache.set(cacheKey, audioBlob);

      return audioBlob;
    } catch (error) {
      console.error('Failed to synthesize text:', error);
      return null;
    }
  }

  /**
   * Create narration for a lap analysis
   * @param {Object} lapAnalysis - Lap analysis data from Gemini
   * @param {Object} lapData - Raw lap telemetry data
   * @returns {Promise<Blob>} Combined audio blob
   */
  async narrateLapAnalysis(lapAnalysis, lapData) {
    const narration = this.constructNarration(lapAnalysis, lapData);
    return await this.synthesizeText(narration);
  }

  /**
   * Construct readable narration from analysis data
   * @private
   */
  constructNarration(lapAnalysis, lapData) {
    if (!lapAnalysis) return '';

    const parts = [];

    // Summary
    if (lapAnalysis.lap_summary) {
      parts.push(`Lap Analysis: ${lapAnalysis.lap_summary}`);
    }

    // Sector breakdown
    if (lapAnalysis.sector_analysis && Array.isArray(lapAnalysis.sector_analysis)) {
      parts.push('Sector Breakdown:');
      lapAnalysis.sector_analysis.forEach(sector => {
        parts.push(`Sector ${sector.sector_number}: ${sector.analysis}`);
      });
    }

    // Key observation
    if (lapAnalysis.key_observation) {
      parts.push(`Key Observation: ${lapAnalysis.key_observation}`);
    }

    // Performance rating
    if (lapAnalysis.performance_rating) {
      const rating = lapAnalysis.performance_rating;
      const ratingText = rating >= 8 ? 'exceptional' : rating >= 7 ? 'strong' : rating >= 5 ? 'consistent' : 'developing';
      parts.push(`Performance Rating: ${rating} out of 10. This lap was ${ratingText}.`);
    }

    return parts.join(' ');
  }

  /**
   * Create audio URL for playback
   * @param {Blob} audioBlob - Audio data blob
   * @returns {string} Object URL for audio element
   */
  createAudioUrl(audioBlob) {
    if (!audioBlob) return null;
    return URL.createObjectURL(audioBlob);
  }

  /**
   * Clean up cached audio
   * @param {string} url - Object URL to revoke
   */
  revokeAudioUrl(url) {
    if (url) {
      URL.revokeObjectURL(url);
    }
  }

  /**
   * Clear entire cache
   */
  clearCache() {
    this.audioCache.clear();
  }

  /**
   * Get supported voices
   * @returns {Promise<Array>} List of available voices
   */
  async getAvailableVoices() {
    if (!this.apiKey) return [];

    try {
      const response = await fetch(`${this.baseUrl}/voices`, {
        headers: {
          'xi-api-key': this.apiKey,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch voices: ${response.statusText}`);
      }

      const data = await response.json();
      return data.voices || [];
    } catch (error) {
      console.error('Failed to get voices:', error);
      return [];
    }
  }
}

export default ElevenLabsService;
