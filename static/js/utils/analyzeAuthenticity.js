/**
 * Analyze the authenticity of news compared to verified articles
 */
async function analyzeAuthenticity() {
    const analyzeButton = document.getElementById('analyze-button');
    const analysisResults = document.getElementById('analysis-results');
    
    try {
        // Show loading state
        analyzeButton.disabled = true;
        analyzeButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        
        // Get original news and verified articles
        const originalNews = document.querySelector('.news-content').textContent;
        const verifiedArticles = Array.from(document.querySelectorAll('.news-card')).map(card => ({
            content: card.querySelector('.description').textContent
        }));
        
        // Make API call
        const response = await fetch('/analyze_authenticity', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                original_news: originalNews,
                verified_articles: verifiedArticles
            }),
        });
        
        if (!response.ok) {
            throw new Error('Failed to analyze authenticity');
        }
        
        const result = await response.json();
        
        // Update UI with the authenticity score
        if (analysisResults) {
            // Update the score percentage
            const scoreElement = document.getElementById('authenticity-score');
            if (scoreElement) {
                scoreElement.textContent = result.authenticity_score;
            }
            
            // Update key findings list
            const findingsList = document.getElementById('key-findings-list');
            if (findingsList && result.key_findings) {
                findingsList.innerHTML = '';
                result.key_findings.forEach(finding => {
                    const li = document.createElement('li');
                    li.textContent = finding;
                    findingsList.appendChild(li);
                });
            }
            
            // Update differences list
            const differencesList = document.getElementById('differences-list');
            if (differencesList && result.differences) {
                differencesList.innerHTML = '';
                result.differences.forEach(difference => {
                    const li = document.createElement('li');
                    li.textContent = difference;
                    differencesList.appendChild(li);
                });
            }
            
            // Update evidence list
            const evidenceList = document.getElementById('evidence-list');
            if (evidenceList && result.supporting_evidence) {
                evidenceList.innerHTML = '';
                result.supporting_evidence.forEach(evidence => {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>"${evidence.quote}"</strong> - <em>${evidence.source}</em>`;
                    evidenceList.appendChild(li);
                });
            }
            
            // Update claims analysis
            const claimsList = document.getElementById('claims-list');
            if (claimsList && result.claims_analysis) {
                claimsList.innerHTML = '';
                result.claims_analysis.forEach(claim => {
                    const claimDiv = document.createElement('div');
                    claimDiv.className = `claim-item claim-${claim.classification}`;
                    
                    const classificationBadge = getClassificationBadge(claim.classification);
                    
                    claimDiv.innerHTML = `
                        <div class="claim-header">
                            <span class="classification-badge ${claim.classification}">${classificationBadge}</span>
                            <span class="confidence">Confidence: ${claim.confidence}%</span>
                        </div>
                        <div class="claim-text">"${claim.claim}"</div>
                        <div class="claim-explanation">
                            <i class="fas fa-info-circle"></i> ${claim.explanation}
                        </div>
                        ${claim.corrected_statement ? `
                        <div class="claim-correction">
                            <i class="fas fa-check"></i> <strong>Correction:</strong> ${claim.corrected_statement}
                        </div>` : ''}
                    `;
                    claimsList.appendChild(claimDiv);
                });
            }
            
            // Update bias detection
            if (result.bias_detection && result.bias_detection.detected) {
                const biasCard = document.getElementById('bias-card');
                const biasType = document.getElementById('bias-type');
                const biasIndicators = document.getElementById('bias-indicators');
                
                if (biasCard) biasCard.style.display = 'block';
                if (biasType) {
                    biasType.textContent = result.bias_detection.type.toUpperCase();
                    biasType.className = `bias-badge bias-${result.bias_detection.type}`;
                }
                if (biasIndicators) {
                    biasIndicators.innerHTML = '';
                    result.bias_detection.indicators.forEach(indicator => {
                        const li = document.createElement('li');
                        li.innerHTML = `<i class="fas fa-angle-right"></i> ${indicator}`;
                        biasIndicators.appendChild(li);
                    });
                }
            }
            
            // Update emotional manipulation
            if (result.emotional_manipulation && result.emotional_manipulation.detected) {
                const manipCard = document.getElementById('manipulation-card');
                const tacticsBadges = document.getElementById('manipulation-tactics');
                const examplesList = document.getElementById('manipulation-examples');
                
                if (manipCard) manipCard.style.display = 'block';
                if (tacticsBadges) {
                    tacticsBadges.innerHTML = '';
                    result.emotional_manipulation.tactics.forEach(tactic => {
                        const badge = document.createElement('span');
                        badge.className = 'tactic-badge';
                        badge.textContent = tactic;
                        tacticsBadges.appendChild(badge);
                    });
                }
                if (examplesList) {
                    examplesList.innerHTML = '';
                    result.emotional_manipulation.examples.forEach(example => {
                        const li = document.createElement('li');
                        li.innerHTML = `<i class="fas fa-quote-left"></i> "${example}"`;
                        examplesList.appendChild(li);
                    });
                }
            }
            
            // Update sensational tone
            if (result.sensational_tone && result.sensational_tone.detected) {
                const sensCard = document.getElementById('sensational-card');
                const scoreFill = document.getElementById('sensational-score-fill');
                const scoreValue = document.getElementById('sensational-score-value');
                const indicators = document.getElementById('sensational-indicators');
                
                if (sensCard) sensCard.style.display = 'block';
                if (scoreFill) scoreFill.style.width = `${result.sensational_tone.score}%`;
                if (scoreValue) scoreValue.textContent = `${result.sensational_tone.score}%`;
                if (indicators) {
                    indicators.innerHTML = '';
                    result.sensational_tone.indicators.forEach(indicator => {
                        const li = document.createElement('li');
                        li.innerHTML = `<i class="fas fa-exclamation"></i> ${indicator}`;
                        indicators.appendChild(li);
                    });
                }
            }
            
            // Show the results
            analysisResults.classList.remove('hidden');
            
            // Update score chart
            updateScoreChart(result.authenticity_score);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during authenticity analysis. Please try again.');
    } finally {
        // Reset button state
        if (analyzeButton) {
            analyzeButton.disabled = false;
            analyzeButton.innerHTML = 'Analyze Authenticity';
        }
    }
}

/**
 * Get display text for claim classification
 */
function getClassificationBadge(classification) {
    const badges = {
        'verified_true': '✓ Verified True',
        'misleading': '⚠ Misleading',
        'false': '✗ False',
        'unverified': '? Unverified'
    };
    return badges[classification] || classification;
}

// Export the function
export default analyzeAuthenticity;
