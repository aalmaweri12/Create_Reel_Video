/**
 * Text-to-Video Tool - Main JavaScript
 * Handles the interactive elements of the web interface
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tab switching
    initTabs();
    
    // Initialize navigation buttons
    initNavigationButtons();
    
    // Initialize advanced options toggle
    initAdvancedOptions();
    
    // Initialize TTS engine selection
    initTTSEngineSelection();
    
    // Initialize form submission and loading indicators
    initFormSubmission();
    
    // Initialize voice selection based on language
    initLanguageSelection();
    
    // Set up file input previews
    initFileInputPreviews();
    
    // Set up automatic cleanup of old files
    scheduleCleanup();
});

/**
 * Initialize tab switching functionality
 */
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');
            
            // Update active tab
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Show the corresponding tab content
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });
}

/**
 * Initialize navigation buttons between tabs
 */
function initNavigationButtons() {
    // Next buttons
    document.getElementById('next-to-settings')?.addEventListener('click', () => {
        document.querySelector('[data-tab="settings"]').click();
    });
    
    document.getElementById('next-to-preview')?.addEventListener('click', () => {
        document.querySelector('[data-tab="preview"]').click();
    });
    
    // Back buttons
    document.getElementById('back-to-story')?.addEventListener('click', () => {
        document.querySelector('[data-tab="story"]').click();
    });
    
    document.getElementById('back-to-settings')?.addEventListener('click', () => {
        document.querySelector('[data-tab="settings"]').click();
    });
}

/**
 * Initialize advanced options toggle
 */
function initAdvancedOptions() {
    const toggle = document.querySelector('.advanced-options-toggle');
    if (toggle) {
        toggle.addEventListener('click', function() {
            const content = document.querySelector('.advanced-options-content');
            if (content.style.display === 'block') {
                content.style.display = 'none';
                this.textContent = 'Advanced Options ▼';
            } else {
                content.style.display = 'block';
                this.textContent = 'Advanced Options ▲';
            }
        });
    }
}

/**
 * Initialize TTS engine selection and related fields
 */
function initTTSEngineSelection() {
    const ttsEngineSelect = document.getElementById('tts-engine');
    if (ttsEngineSelect) {
        ttsEngineSelect.addEventListener('change', function() {
            updateTTSEngineOptions(this.value);
        });
        
        // Initial setup
        updateTTSEngineOptions(ttsEngineSelect.value);
    }
}

/**
 * Update the visible options based on the selected TTS engine
 */
function updateTTSEngineOptions(engineType) {
    const apiKeyGroup = document.getElementById('api-key-group');
    const voiceSelection = document.getElementById('voice-selection');
    
    if (engineType === 'google_cloud') {
        if (apiKeyGroup) apiKeyGroup.style.display = 'block';
        if (voiceSelection) {
            voiceSelection.style.display = 'block';
            loadVoices('google_cloud');
        }
    } else if (engineType === 'pyttsx3') {
        if (apiKeyGroup) apiKeyGroup.style.display = 'none';
        if (voiceSelection) {
            voiceSelection.style.display = 'block';
            loadVoices('pyttsx3');
        }
    } else {
        if (apiKeyGroup) apiKeyGroup.style.display = 'none';
        if (voiceSelection) voiceSelection.style.display = 'none';
    }
}

/**
 * Initialize form submission handling
 */
function initFormSubmission() {
    const form = document.getElementById('generator-form');
    const loading = document.getElementById('loading');
    
    if (form && loading) {
        form.addEventListener('submit', function() {
            // Validate form inputs
            if (!validateForm(this)) {
                return false;
            }
            
            // Show loading indicator
            loading.style.display = 'block';
            
            // Simulate progress (will be replaced by actual progress updates in production)
            simulateProgress();
            
            return true;
        });
    }
}

/**
 * Validate form inputs before submission
 */
function validateForm(form) {
    const text = form.querySelector('#text').value.trim();
    if (!text) {
        alert('Please enter your story text');
        document.querySelector('[data-tab="story"]').click();
        return false;
    }
    
    const videoInput = form.querySelector('#background-video');
    if (videoInput && !videoInput.files.length) {
        alert('Please upload a background video');
        document.querySelector('[data-tab="story"]').click();
        return false;
    }
    
    const ttsEngine = form.querySelector('#tts-engine').value;
    if (ttsEngine === 'google_cloud') {
        const apiKeyInput = form.querySelector('#api-key');
        if (apiKeyInput && !apiKeyInput.files.length) {
            alert('Please upload a Google Cloud API key file for the selected TTS engine');
            document.querySelector('[data-tab="settings"]').click();
            return false;
        }
    }
    
    return true;
}

/**
 * Simulate progress for the loading indicator
 * In a production environment, this would be replaced with actual progress updates
 */
function simulateProgress() {
    let progress = 0;
    const bar = document.getElementById('progress-bar');
    const text = document.getElementById('progress-text');
    
    if (!bar || !text) return;
    
    const interval = setInterval(function() {
        progress += Math.random() * 5;
        if (progress > 100) progress = 100;
        
        bar.style.width = progress + '%';
        
        if (progress < 20) {
            text.textContent = 'Processing story text...';
        } else if (progress < 40) {
            text.textContent = 'Generating speech...';
        } else if (progress < 60) {
            text.textContent = 'Creating captions...';
        } else if (progress < 80) {
            text.textContent = 'Processing video...';
        } else {
            text.textContent = 'Finalizing...';
        }
        
        if (progress === 100) {
            clearInterval(interval);
        }
    }, 500);
}

/**
 * Load voice options based on the selected TTS engine and language
 */
function loadVoices(engine) {
    const voiceSelect = document.getElementById('voice');
    const languageSelect = document.getElementById('language');
    const apiKeyInput = document.getElementById('api-key');
    
    if (!voiceSelect) return;
    
    // Clear current options
    voiceSelect.innerHTML = '<option value="">Default Voice</option>';
    
    // For a fully implemented version, this would make an AJAX call to the server
    // to get the available voices for the selected engine and language
    if (engine === 'google_cloud') {
        // In a real implementation, we would send the API key and language to the server
        // For now, just add some example voices
        const exampleVoices = {
            'en': [
                {id: 'en-US-Neural2-A', name: 'Male Voice 1'},
                {id: 'en-US-Neural2-C', name: 'Male Voice 2'},
                {id: 'en-US-Neural2-D', name: 'Male Voice 3'},
                {id: 'en-US-Neural2-E', name: 'Female Voice 1'},
                {id: 'en-US-Neural2-F', name: 'Female Voice 2'}
            ],
            'es': [
                {id: 'es-ES-Neural2-A', name: 'Spanish Male Voice'},
                {id: 'es-ES-Neural2-B', name: 'Spanish Female Voice'}
            ],
            'fr': [
                {id: 'fr-FR-Neural2-A', name: 'French Male Voice'},
                {id: 'fr-FR-Neural2-B', name: 'French Female Voice'}
            ]
        };
        
        const language = languageSelect ? languageSelect.value : 'en';
        const voices = exampleVoices[language] || exampleVoices['en'];
        
        voices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.id;
            option.textContent = voice.name;
            voiceSelect.appendChild(option);
        });
    } else if (engine === 'pyttsx3') {
        // For pyttsx3, we would ideally query the system for available voices
        // For now, just add some example voices
        const voices = [
            {id: 'voice1', name: 'System Voice 1'},
            {id: 'voice2', name: 'System Voice 2'}
        ];
        
        voices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.id;
            option.textContent = voice.name;
            voiceSelect.appendChild(option);
        });
    }
    
    // In a real implementation, we would make an AJAX call like this:
    /*
    // Create form data
    const formData = new FormData();
    formData.append('tts_engine', engine);
    formData.append('language', languageSelect ? languageSelect.value : 'en');
    
    // Add API key if available
    if (apiKeyInput && apiKeyInput.files.length > 0) {
        formData.append('api_key', apiKeyInput.files[0]);
    }
    
    // Make AJAX call to get voices
    fetch('/list_voices', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error loading voices:', data.error);
            return;
        }
        
        // Add voices to select
        if (data.voices && Array.isArray(data.voices)) {
            data.voices.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice.id || voice;
                option.textContent = voice.name || voice;
                voiceSelect.appendChild(option);
            });
        }
    })
    .catch(error => {
        console.error('Error loading voices:', error);
    });
    */
}

/**
 * Initialize language selection change handler
 */
function initLanguageSelection() {
    const languageSelect = document.getElementById('language');
    const ttsEngineSelect = document.getElementById('tts-engine');
    
    if (languageSelect && ttsEngineSelect) {
        languageSelect.addEventListener('change', function() {
            // If Google Cloud TTS is selected, reload voices for the new language
            if (ttsEngineSelect.value === 'google_cloud') {
                loadVoices('google_cloud');
            }
        });
    }
}

/**
 * Initialize file input previews
 */
function initFileInputPreviews() {
    // For video preview
    const videoInput = document.getElementById('background-video');
    const previewImage = document.getElementById('preview-image');
    
    if (videoInput && previewImage) {
        videoInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                // If browser supports it, create a video preview
                try {
                    const url = URL.createObjectURL(this.files[0]);
                    
                    // Create a video element to extract a frame
                    const video = document.createElement('video');
                    video.src = url;
                    video.currentTime = 1; // Seek to 1 second
                    
                    video.addEventListener('loadeddata', function() {
                        // Create a canvas to capture the frame
                        const canvas = document.createElement('canvas');
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                        
                        // Draw the video frame on the canvas
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        
                        // Set the canvas as the preview image
                        previewImage.src = canvas.toDataURL();
                        
                        // Clean up
                        URL.revokeObjectURL(url);
                    });
                    
                    video.addEventListener('error', function() {
                        // Fallback to a generic video icon
                        previewImage.src = '/static/img/video-placeholder.jpg';
                    });
                } catch (e) {
                    console.error('Error creating video preview:', e);
                    // Fallback to a generic video icon
                    previewImage.src = '/static/img/video-placeholder.jpg';
                }
            }
        });
    }
}

/**
 * Schedule a cleanup of old files
 */
function scheduleCleanup() {
    // Run cleanup once per session after 10 minutes
    setTimeout(function() {
        fetch('/cleanup', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Cleanup status:', data.status);
        })
        .catch(error => {
            console.error('Error during cleanup:', error);
        });
    }, 10 * 60 * 1000); // 10 minutes
}