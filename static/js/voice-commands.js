/**
 * Voice Commands Manager
 *
 * Handles voice input using Web Speech API and processes commands
 * through the backend API.
 */

class VoiceCommandManager {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.transcript = '';
        this.confidence = 0;
        this.modal = null;
        this.button = null;

        // Initialize if browser supports Web Speech API
        this.initializeSpeechRecognition();
        this.initializeUI();
        this.setupKeyboardShortcut();
    }

    initializeSpeechRecognition() {
        // Check browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            console.warn('Web Speech API not supported in this browser');
            this.showBrowserNotSupported();
            return;
        }

        // Initialize recognition
        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'en-US';
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;

        // Event handlers
        this.recognition.onstart = () => this.onRecognitionStart();
        this.recognition.onresult = (event) => this.onRecognitionResult(event);
        this.recognition.onerror = (event) => this.onRecognitionError(event);
        this.recognition.onend = () => this.onRecognitionEnd();
    }

    initializeUI() {
        // Create floating voice button
        this.createVoiceButton();

        // Create voice modal
        this.createVoiceModal();

        // Add to page
        document.body.appendChild(this.button);
        document.body.appendChild(this.modal);
    }

    createVoiceButton() {
        this.button = document.createElement('button');
        this.button.id = 'voice-command-button';
        this.button.className = 'voice-btn';
        this.button.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                <line x1="12" y1="19" x2="12" y2="23"></line>
                <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
        `;
        this.button.title = 'Voice Command (Ctrl+Shift+V)';
        this.button.setAttribute('aria-label', 'Activate voice command');

        this.button.addEventListener('click', () => this.toggleListening());
    }

    createVoiceModal() {
        this.modal = document.createElement('div');
        this.modal.id = 'voice-command-modal';
        this.modal.className = 'voice-modal';
        this.modal.innerHTML = `
            <div class="voice-modal-content">
                <div class="voice-modal-header">
                    <h3>Voice Command</h3>
                    <button class="voice-modal-close" aria-label="Close">&times;</button>
                </div>
                <div class="voice-modal-body">
                    <div class="voice-status">
                        <div class="voice-animation">
                            <div class="voice-wave"></div>
                            <div class="voice-wave"></div>
                            <div class="voice-wave"></div>
                            <div class="voice-wave"></div>
                            <div class="voice-wave"></div>
                        </div>
                        <p class="voice-status-text">Listening...</p>
                    </div>
                    <div class="voice-transcript">
                        <p class="transcript-text"></p>
                    </div>
                    <div class="voice-confirmation" style="display: none;">
                        <div class="confirmation-content">
                            <p class="confirmation-message"></p>
                            <div class="confirmation-buttons">
                                <button class="btn btn-primary confirm-btn">Confirm</button>
                                <button class="btn btn-secondary cancel-btn">Cancel</button>
                            </div>
                        </div>
                    </div>
                    <div class="voice-error" style="display: none;">
                        <p class="error-text"></p>
                        <button class="btn btn-secondary retry-btn">Try Again</button>
                    </div>
                </div>
                <div class="voice-modal-footer">
                    <small>Try: "Add expense 50 dollars for groceries" or "What's my total this month?"</small>
                </div>
            </div>
        `;

        // Event listeners
        this.modal.querySelector('.voice-modal-close').addEventListener('click', () => this.closeModal());
        this.modal.querySelector('.cancel-btn').addEventListener('click', () => this.closeModal());
        this.modal.querySelector('.retry-btn').addEventListener('click', () => this.retryListening());
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
    }

    setupKeyboardShortcut() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + V
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'V') {
                e.preventDefault();
                this.toggleListening();
            }
        });
    }

    toggleListening() {
        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    startListening() {
        if (!this.recognition) {
            this.showBrowserNotSupported();
            return;
        }

        // Reset state
        this.transcript = '';
        this.confidence = 0;

        // Show modal
        this.showModal();
        this.showListeningState();

        // Start recognition
        try {
            this.recognition.start();
            this.isListening = true;
            this.button.classList.add('listening');
        } catch (error) {
            console.error('Error starting recognition:', error);
            this.showError('Failed to start voice recognition. Please try again.');
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
            this.button.classList.remove('listening');
        }
    }

    onRecognitionStart() {
        console.log('Voice recognition started');
    }

    onRecognitionResult(event) {
        // Get the transcript
        const result = event.results[event.results.length - 1];
        const transcript = result[0].transcript;
        const isFinal = result.isFinal;

        // Update transcript display
        this.updateTranscript(transcript);

        if (isFinal) {
            this.transcript = transcript;
            this.confidence = result[0].confidence;
            console.log('Final transcript:', transcript, 'Confidence:', this.confidence);

            // Process the command
            this.processCommand(transcript);
        }
    }

    onRecognitionError(event) {
        console.error('Recognition error:', event.error);

        let errorMessage = 'An error occurred with voice recognition.';
        switch (event.error) {
            case 'no-speech':
                errorMessage = "I didn't hear anything. Please try again.";
                break;
            case 'audio-capture':
                errorMessage = 'No microphone was found. Please check your microphone.';
                break;
            case 'not-allowed':
                errorMessage = 'Microphone permission denied. Please enable microphone access.';
                break;
            case 'network':
                errorMessage = 'Network error occurred. Please check your connection.';
                break;
            case 'aborted':
                errorMessage = 'Voice recognition was aborted.';
                break;
        }

        this.showError(errorMessage);
    }

    onRecognitionEnd() {
        this.isListening = false;
        this.button.classList.remove('listening');
        console.log('Voice recognition ended');
    }

    updateTranscript(text) {
        const transcriptEl = this.modal.querySelector('.transcript-text');
        transcriptEl.textContent = text;
    }

    async processCommand(commandText) {
        // Show processing state
        this.showProcessingState();

        try {
            // Send to backend API
            const response = await fetch('/api/voice/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: commandText })
            });

            const data = await response.json();

            if (data.success) {
                // Show confirmation
                this.showConfirmation(data);
            } else {
                // Show error
                this.showError(data.message || 'Command not understood');
            }
        } catch (error) {
            console.error('Error processing command:', error);
            this.showError('Failed to process command. Please try again.');
        }
    }

    showConfirmation(data) {
        // Hide other states
        this.modal.querySelector('.voice-status').style.display = 'none';
        this.modal.querySelector('.voice-transcript').style.display = 'none';
        this.modal.querySelector('.voice-error').style.display = 'none';

        // Show confirmation
        const confirmationEl = this.modal.querySelector('.voice-confirmation');
        confirmationEl.style.display = 'block';

        const messageEl = confirmationEl.querySelector('.confirmation-message');
        messageEl.textContent = data.message;

        // Setup confirm button
        const confirmBtn = confirmationEl.querySelector('.confirm-btn');
        confirmBtn.onclick = async () => {
            await this.executeCommand(data);
        };

        // Speak the confirmation
        this.speak(data.message);
    }

    async executeCommand(data) {
        // Command already executed by backend, just show success and close
        this.showSuccess(data.message);

        // Refresh the page after a short delay if entry was added
        if (data.intent === 'add_expense' || data.intent === 'add_income') {
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else if (data.intent === 'delete_entry') {
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            setTimeout(() => {
                this.closeModal();
            }, 2000);
        }
    }

    showSuccess(message) {
        // Show success state
        this.modal.querySelector('.voice-status').style.display = 'none';
        this.modal.querySelector('.voice-transcript').style.display = 'none';
        this.modal.querySelector('.voice-confirmation').style.display = 'none';
        this.modal.querySelector('.voice-error').style.display = 'none';

        // Create success message
        const bodyEl = this.modal.querySelector('.voice-modal-body');
        bodyEl.innerHTML = `
            <div class="voice-success">
                <svg class="success-icon" xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <p class="success-text">${message}</p>
            </div>
        `;
    }

    showError(message) {
        // Hide other states
        this.modal.querySelector('.voice-status').style.display = 'none';
        this.modal.querySelector('.voice-transcript').style.display = 'none';
        this.modal.querySelector('.voice-confirmation').style.display = 'none';

        // Show error
        const errorEl = this.modal.querySelector('.voice-error');
        errorEl.style.display = 'block';
        errorEl.querySelector('.error-text').textContent = message;

        // Speak the error
        this.speak(message);
    }

    showListeningState() {
        this.modal.querySelector('.voice-status').style.display = 'block';
        this.modal.querySelector('.voice-transcript').style.display = 'block';
        this.modal.querySelector('.voice-confirmation').style.display = 'none';
        this.modal.querySelector('.voice-error').style.display = 'none';
        this.modal.querySelector('.voice-status-text').textContent = 'Listening...';
    }

    showProcessingState() {
        this.modal.querySelector('.voice-status-text').textContent = 'Processing...';
    }

    retryListening() {
        this.startListening();
    }

    showModal() {
        this.modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        this.stopListening();
        this.modal.classList.remove('show');
        document.body.style.overflow = '';
    }

    speak(text) {
        // Use Speech Synthesis API for voice feedback
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 0.8;
            window.speechSynthesis.speak(utterance);
        }
    }

    showBrowserNotSupported() {
        // Hide the voice button if not supported
        if (this.button) {
            this.button.style.display = 'none';
        }

        console.warn('Voice commands not available in this browser. Please use Chrome, Edge, Opera, or Safari.');
    }
}

// Initialize voice command manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if user is logged in (check for specific element or session)
    if (document.querySelector('[data-user-authenticated]') || document.body.classList.contains('authenticated')) {
        window.voiceCommandManager = new VoiceCommandManager();
    }
});
