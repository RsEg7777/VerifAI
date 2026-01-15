/**
 * Text Verification Utility
 * Handles WhatsApp forward and social media text verification
 */

let detectTimeout = null;

// Debounced language detection
window.detectInputLanguage = async function() {
    const textInput = document.getElementById('text-input');
    const langName = document.getElementById('lang-name');
    
    if (!textInput || !langName) return;
    
    const text = textInput.value.trim();
    
    if (text.length < 10) {
        langName.textContent = '-';
        return;
    }
    
    // Debounce the API call
    clearTimeout(detectTimeout);
    detectTimeout = setTimeout(async () => {
        try {
            const response = await fetch('/detect_language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            
            if (response.ok) {
                const data = await response.json();
                langName.textContent = data.language_name || 'Unknown';
            }
        } catch (error) {
            console.error('Language detection error:', error);
            langName.textContent = 'Unknown';
        }
    }, 500);
};

// Main verification function
window.verifyText = async function() {
    const textInput = document.getElementById('text-input');
    const verifyBtn = document.getElementById('verify-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const resultsSection = document.getElementById('results-section');
    
    if (!textInput) return;
    
    const text = textInput.value.trim();
    
    if (!text) {
        alert('Please enter some text to verify');
        return;
    }
    
    if (text.length < 20) {
        alert('Please enter more text for accurate verification (at least 20 characters)');
        return;
    }
    
    // Show loading
    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    loadingOverlay.classList.add('visible');
    
    try {
        const response = await fetch('/verify_text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayResults(data);
        } else {
            throw new Error(data.error || 'Verification failed');
        }
        
    } catch (error) {
        console.error('Verification error:', error);
        alert('Error verifying text: ' + error.message);
    } finally {
        // Reset button
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '<i class="fas fa-search"></i> Verify Message';
        loadingOverlay.classList.remove('visible');
    }
};

// Display verification results
function displayResults(data) {
    const resultsSection = document.getElementById('results-section');
    
    // Show results section
    resultsSection.classList.add('visible');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Update verdict badge
    const verdictBadge = document.getElementById('verdict-badge');
    const verdictText = document.getElementById('verdict-text');
    const verdict = data.verdict || 'Needs Verification';
    
    // Remove old classes
    verdictBadge.className = 'verdict-badge';
    
    // Add appropriate class based on verdict
    if (verdict.toLowerCase().includes('true')) {
        verdictBadge.classList.add('likely-true');
        verdictBadge.innerHTML = `<i class="fas fa-check-circle"></i><span>${verdict}</span>`;
    } else if (verdict.toLowerCase().includes('verification')) {
        verdictBadge.classList.add('needs-verification');
        verdictBadge.innerHTML = `<i class="fas fa-question-circle"></i><span>${verdict}</span>`;
    } else if (verdict.toLowerCase().includes('misinformation')) {
        verdictBadge.classList.add('misinformation');
        verdictBadge.innerHTML = `<i class="fas fa-times-circle"></i><span>${verdict}</span>`;
    } else {
        verdictBadge.classList.add('likely-false');
        verdictBadge.innerHTML = `<i class="fas fa-exclamation-circle"></i><span>${verdict}</span>`;
    }
    
    // Update credibility score
    document.getElementById('credibility-score').textContent = data.credibility_score || 0;
    
    // Update summary
    document.getElementById('summary-text').textContent = data.summary || '';
    
    // Update claims list
    const claimsList = document.getElementById('claims-list');
    claimsList.innerHTML = '';
    
    if (data.claims && data.claims.length > 0) {
        data.claims.forEach(claim => {
            const li = document.createElement('li');
            li.className = `claim-item ${claim.assessment}`;
            li.innerHTML = `
                <div class="claim-text">"${claim.claim}"</div>
                <span class="claim-assessment ${claim.assessment}">${formatAssessment(claim.assessment)}</span>
                <div class="claim-explanation">${claim.explanation || ''}</div>
            `;
            claimsList.appendChild(li);
        });
    } else {
        claimsList.innerHTML = '<li class="claim-item unverified"><div class="claim-text">No specific claims identified</div></li>';
    }
    
    // Update red flags
    const redFlagsCard = document.getElementById('red-flags-card');
    const redFlagsList = document.getElementById('red-flags-list');
    redFlagsList.innerHTML = '';
    
    if (data.red_flags && data.red_flags.length > 0) {
        redFlagsCard.style.display = 'block';
        data.red_flags.forEach(flag => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fas fa-flag"></i><span>${flag}</span>`;
            redFlagsList.appendChild(li);
        });
    } else {
        redFlagsCard.style.display = 'none';
    }
    
    // Update recommendations
    const recommendationsList = document.getElementById('recommendations-list');
    recommendationsList.innerHTML = '';
    
    if (data.recommendations && data.recommendations.length > 0) {
        data.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fas fa-lightbulb"></i><span>${rec}</span>`;
            recommendationsList.appendChild(li);
        });
    } else {
        recommendationsList.innerHTML = '<li><i class="fas fa-lightbulb"></i><span>Cross-verify with official sources</span></li>';
    }
}

// Format assessment label
function formatAssessment(assessment) {
    const labels = {
        'true': '✓ True',
        'false': '✗ False',
        'misleading': '⚠ Misleading',
        'unverified': '? Unverified'
    };
    return labels[assessment] || assessment;
}
