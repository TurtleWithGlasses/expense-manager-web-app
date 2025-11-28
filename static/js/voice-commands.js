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
        this.debugMode = true; // Enable debug logging
        this.hasReceivedSpeech = false; // Track if we got any speech
        this.hasReceivedAnyResult = false; // Track if we got ANY result (even unclear)
        this.silenceTimeout = null; // Timeout for stopping after silence
        this.startTimeout = null; // Timeout for detecting if start event never fires
        this.recognitionStarted = false; // Track if onstart event actually fired

        console.log('[Voice Commands] Initializing VoiceCommandManager...');

        // Initialize if browser supports Web Speech API
        this.initializeSpeechRecognition();
        this.initializeUI();
        this.setupKeyboardShortcut();

        console.log('[Voice Commands] Initialization complete');
    }

    initializeSpeechRecognition() {
        console.log('[Voice Commands] Checking browser support...');

        // Check browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            console.error('[Voice Commands] ❌ Web Speech API NOT supported in this browser');
            console.log('[Voice Commands] Browser info:', navigator.userAgent);
            this.showBrowserNotSupported();
            return;
        }

        console.log('[Voice Commands] ✅ Web Speech API is supported');

        // Initialize recognition
        this.recognition = new SpeechRecognition();
        this.recognition.lang = 'en-US';
        this.recognition.continuous = true; // Keep listening for longer
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 1;

        console.log('[Voice Commands] SpeechRecognition configured:', {
            lang: this.recognition.lang,
            continuous: this.recognition.continuous,
            interimResults: this.recognition.interimResults,
            maxAlternatives: this.recognition.maxAlternatives
        });

        // Event handlers
        this.recognition.onstart = () => this.onRecognitionStart();
        this.recognition.onresult = (event) => this.onRecognitionResult(event);
        this.recognition.onerror = (event) => this.onRecognitionError(event);
        this.recognition.onend = () => this.onRecognitionEnd();

        console.log('[Voice Commands] Event handlers attached');

        // Update debug panel
        this.updateDebugPanel('api-support', this.recognition ? '✅ Supported' : '❌ Not supported');
    }

    updateDebugPanel(field, value, color = null) {
        // Update debug panel in modal if it exists
        if (!this.modal) return;

        const fieldMap = {
            'api-support': 'debug-api-support',
            'mic-status': 'debug-mic-status',
            'listening-status': 'debug-listening-status',
            'voice-activity': 'debug-voice-activity',
            'last-event': 'debug-last-event'
        };

        const elementId = fieldMap[field];
        if (!elementId) return;

        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            if (color) {
                element.style.color = color;
            }
        }

        // Update indicator color based on status
        const indicator = document.getElementById('debug-status-indicator');
        if (indicator && this.isListening) {
            indicator.style.background = '#28a745'; // Green when listening
        } else if (indicator) {
            indicator.style.background = '#6c757d'; // Gray when not listening
        }
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
                    <div class="voice-debug-panel" style="background: var(--surface-secondary); border-radius: 8px; padding: 12px; margin-bottom: 16px; font-size: 12px; font-family: monospace;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <strong style="color: var(--text-primary);">Debug Status</strong>
                            <span id="debug-status-indicator" style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #6c757d;"></span>
                        </div>
                        <div style="color: var(--text-secondary); line-height: 1.5;">
                            <div>API Support: <span id="debug-api-support" style="color: var(--text-primary);">Checking...</span></div>
                            <div>Microphone: <span id="debug-mic-status" style="color: var(--text-primary);">Not started</span></div>
                            <div>Listening: <span id="debug-listening-status" style="color: var(--text-primary);">No</span></div>
                            <div>Voice Activity: <span id="debug-voice-activity" style="color: var(--text-primary);">None</span></div>
                            <div>Last Event: <span id="debug-last-event" style="color: var(--text-primary);">None</span></div>
                        </div>
                    </div>
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
                    <br>
                    <small style="color: var(--text-secondary); margin-top: 4px; display: block;">💡 Check browser console (F12) for detailed logs</small>
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
        console.log('[Voice Commands] 🎤 Starting voice recognition...');

        if (!this.recognition) {
            console.error('[Voice Commands] ❌ Recognition not initialized');
            this.showBrowserNotSupported();
            return;
        }

        // Reset state
        this.transcript = '';
        this.confidence = 0;
        this.hasReceivedSpeech = false;
        this.hasReceivedAnyResult = false;
        this.recognitionStarted = false;

        // Clear any existing timeouts
        if (this.silenceTimeout) {
            clearTimeout(this.silenceTimeout);
            this.silenceTimeout = null;
        }
        if (this.startTimeout) {
            clearTimeout(this.startTimeout);
            this.startTimeout = null;
        }

        console.log('[Voice Commands] State reset, showing modal...');

        // Show modal
        this.showModal();
        this.showListeningState();

        // Initialize debug status
        this.updateDebugPanel('mic-status', '⏳ Starting...', '#ffc107');
        this.updateDebugPanel('listening-status', '⏳ Starting...', '#ffc107');
        this.updateDebugPanel('last-event', 'Initializing...');

        // Start recognition
        try {
            console.log('[Voice Commands] Calling recognition.start()...');
            this.recognition.start();
            this.isListening = true;
            this.button.classList.add('listening');
            console.log('[Voice Commands] ✅ Recognition.start() called successfully');

            // Set a timeout to detect if onstart event never fires
            this.startTimeout = setTimeout(() => {
                if (!this.recognitionStarted) {
                    console.error('[Voice Commands] ❌ TIMEOUT: onstart event never fired after 3 seconds');
                    console.error('[Voice Commands] Recognition.start() was called but onstart event did not trigger');
                    console.error('[Voice Commands] This indicates a Web Speech API initialization failure');

                    this.updateDebugPanel('mic-status', '❌ Failed', '#dc3545');
                    this.updateDebugPanel('listening-status', '❌ No', '#dc3545');
                    this.updateDebugPanel('last-event', 'ERROR: onstart never fired');

                    this.stopListening();
                    this.showError('Voice recognition failed to start. The microphone may be in use by another application. Please close other apps using the microphone and try again.');
                }
            }, 3000); // Wait 3 seconds for onstart event

        } catch (error) {
            console.error('[Voice Commands] ❌ Error calling recognition.start():', error);
            console.error('[Voice Commands] Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            this.showError('Failed to start voice recognition. Please try again.');
        }
    }

    stopListening() {
        // Clear start timeout if still running
        if (this.startTimeout) {
            clearTimeout(this.startTimeout);
            this.startTimeout = null;
        }

        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
            this.button.classList.remove('listening');
        }
    }

    onRecognitionStart() {
        console.log('[Voice Commands] 🟢 onstart event fired - Recognition is now active');
        console.log('[Voice Commands] Microphone should be listening now');

        // Mark that onstart actually fired
        this.recognitionStarted = true;

        // Clear the start timeout since onstart fired successfully
        if (this.startTimeout) {
            clearTimeout(this.startTimeout);
            this.startTimeout = null;
            console.log('[Voice Commands] ✅ Start timeout cleared - onstart fired in time');
        }

        this.updateDebugPanel('mic-status', '✅ Active', '#28a745');
        this.updateDebugPanel('listening-status', '✅ Yes', '#28a745');
        this.updateDebugPanel('last-event', 'onstart');
    }

    onRecognitionResult(event) {
        console.log('[Voice Commands] 📝 onresult event fired');
        console.log('[Voice Commands] Number of results:', event.results.length);

        // Mark that we received ANY result (even if unclear)
        this.hasReceivedAnyResult = true;
        this.updateDebugPanel('voice-activity', '✅ Detected', '#28a745');
        this.updateDebugPanel('last-event', 'onresult (voice activity detected!)');

        // Get the transcript
        const result = event.results[event.results.length - 1];
        const transcript = result[0].transcript;
        const isFinal = result.isFinal;
        const confidence = result[0].confidence;

        console.log('[Voice Commands] Transcript:', transcript);
        console.log('[Voice Commands] Transcript length:', transcript.length);
        console.log('[Voice Commands] Is final:', isFinal);
        console.log('[Voice Commands] Confidence:', confidence);

        // Check if we got actual meaningful speech
        const hasContent = transcript && transcript.trim().length > 0;
        if (hasContent) {
            this.hasReceivedSpeech = true;
            this.updateDebugPanel('voice-activity', '✅ Clear Speech', '#28a745');
            console.log('[Voice Commands] ✅ Meaningful speech detected');
        } else {
            this.updateDebugPanel('voice-activity', '⚠️ Unclear', '#ffc107');
            console.log('[Voice Commands] ⚠️ Voice detected but no clear words');
        }

        // Update transcript display
        this.updateTranscript(transcript);

        if (isFinal) {
            this.transcript = transcript;
            this.confidence = confidence;
            console.log('[Voice Commands] ✅ Final result received');
            console.log('[Voice Commands] Transcript:', transcript || '(empty)');
            console.log('[Voice Commands] Confidence score:', this.confidence);

            if (hasContent) {
                this.updateDebugPanel('last-event', `Final: "${transcript.substring(0, 30)}..."`);

                // Stop listening after getting final result
                console.log('[Voice Commands] Stopping recognition after final result');
                this.stopListening();

                // Process the command
                this.processCommand(transcript);
            } else {
                // Got voice activity but no clear speech
                console.warn('[Voice Commands] ⚠️ Final result is empty - voice detected but speech unclear');
                this.updateDebugPanel('last-event', 'Voice heard but unclear');
                this.stopListening();
                this.showError("I heard you speaking but couldn't understand the words. Please speak more clearly and try again.");
            }
        } else {
            console.log('[Voice Commands] ⏳ Interim result (not final yet)');
            this.updateDebugPanel('last-event', 'Interim result...');
        }
    }

    onRecognitionError(event) {
        console.error('[Voice Commands] ❌ onerror event fired');
        console.error('[Voice Commands] Error type:', event.error);
        console.error('[Voice Commands] Error event:', event);

        let errorMessage = 'An error occurred with voice recognition.';
        let debugInfo = '';

        switch (event.error) {
            case 'no-speech':
                errorMessage = "I didn't hear anything. Please try again.";
                debugInfo = 'Microphone is active but no speech was detected. Try speaking louder or closer to the microphone.';
                break;
            case 'audio-capture':
                errorMessage = 'No microphone was found. Please check your microphone.';
                debugInfo = 'Browser cannot access any audio input device. Check device manager and browser permissions.';
                break;
            case 'not-allowed':
                errorMessage = 'Microphone permission denied. Please enable microphone access.';
                debugInfo = 'User denied microphone permission or browser blocked it. Check browser address bar for permission icon.';
                break;
            case 'network':
                errorMessage = 'Network error occurred. Please check your connection.';
                debugInfo = 'Speech recognition service requires internet connection.';
                break;
            case 'aborted':
                errorMessage = 'Voice recognition was aborted.';
                debugInfo = 'Recognition was stopped before completion.';
                break;
            default:
                debugInfo = `Unknown error: ${event.error}`;
        }

        console.error('[Voice Commands] Error message:', errorMessage);
        console.error('[Voice Commands] Debug info:', debugInfo);

        this.updateDebugPanel('last-event', `❌ Error: ${event.error}`, '#dc3545');
        this.updateDebugPanel('mic-status', '❌ Error', '#dc3545');
        this.updateDebugPanel('listening-status', '❌ No', '#dc3545');

        this.showError(errorMessage);
    }

    onRecognitionEnd() {
        console.log('[Voice Commands] 🔴 onend event fired - Recognition stopped');
        console.log('[Voice Commands] Was listening:', this.isListening);
        console.log('[Voice Commands] Final transcript:', this.transcript || '(none)');
        console.log('[Voice Commands] Had received any result:', this.hasReceivedAnyResult);
        console.log('[Voice Commands] Had received speech:', this.hasReceivedSpeech);

        this.isListening = false;
        this.button.classList.remove('listening');

        this.updateDebugPanel('mic-status', 'Stopped', '#6c757d');
        this.updateDebugPanel('listening-status', 'No', '#6c757d');

        // Provide specific feedback based on what we detected
        if (!this.hasReceivedSpeech && !this.transcript) {
            if (this.hasReceivedAnyResult) {
                // We detected voice activity but couldn't understand the words
                console.warn('[Voice Commands] ⚠️ Voice activity detected but speech was unclear');
                this.updateDebugPanel('last-event', 'onend (voice heard but unclear)');
                this.showError("I heard you speaking but couldn't make out the words. Please speak more clearly and closer to the microphone.");
            } else {
                // No voice activity detected at all
                console.warn('[Voice Commands] ⚠️ No voice activity detected');
                this.updateDebugPanel('last-event', 'onend (no sound detected)');
                this.showError("I didn't hear anything. Please check your microphone and speak louder.");
            }
        }
    }

    updateTranscript(text) {
        const transcriptEl = this.modal.querySelector('.transcript-text');
        transcriptEl.textContent = text;
    }

    async processCommand(commandText) {
        console.log('[Voice Commands] 🔄 Processing command:', commandText);

        // Show processing state
        this.showProcessingState();

        try {
            console.log('[Voice Commands] Sending to backend API...');

            // Send to backend API
            const response = await fetch('/api/voice/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: commandText })
            });

            console.log('[Voice Commands] API response status:', response.status);

            const data = await response.json();
            console.log('[Voice Commands] API response data:', data);

            if (data.success) {
                console.log('[Voice Commands] ✅ Command processed successfully');
                console.log('[Voice Commands] Intent:', data.intent);
                console.log('[Voice Commands] Message:', data.message);

                // Show confirmation
                this.showConfirmation(data);
            } else {
                console.warn('[Voice Commands] ⚠️ Command not understood');
                console.warn('[Voice Commands] Error message:', data.message);

                // Show error
                this.showError(data.message || 'Command not understood');
            }
        } catch (error) {
            console.error('[Voice Commands] ❌ Error processing command:', error);
            console.error('[Voice Commands] Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
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
    console.log('[Voice Commands] DOM loaded, checking authentication...');

    // Only initialize if user is logged in (check for specific element or session)
    const isAuthenticated = document.querySelector('[data-user-authenticated]') || document.body.classList.contains('authenticated');

    console.log('[Voice Commands] Is authenticated:', isAuthenticated);

    if (isAuthenticated) {
        console.log('[Voice Commands] Creating VoiceCommandManager instance...');
        window.voiceCommandManager = new VoiceCommandManager();
        console.log('[Voice Commands] ✅ Manager instance created and available as window.voiceCommandManager');
    } else {
        console.log('[Voice Commands] ⚠️ User not authenticated, voice commands disabled');
    }
});
