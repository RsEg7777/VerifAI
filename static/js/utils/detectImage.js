/**
 * Image Detection Utility
 * Handles image upload and AI detection analysis
 */

let selectedFile = null;

// Handle image selection
document.getElementById('image-input').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        selectedFile = file;
        
        // Validate file type
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Please select a valid image file (PNG, JPG, JPEG, GIF, WEBP)');
            return;
        }
        
        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert('File size must be less than 10MB');
            return;
        }
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('preview-image').src = e.target.result;
            document.getElementById('preview-section').classList.add('visible');
            document.getElementById('results-section').classList.remove('visible');
        };
        reader.readAsDataURL(file);
    }
});

// Handle drag and drop
const uploadSection = document.getElementById('upload-section');

uploadSection.addEventListener('dragover', function(e) {
    e.preventDefault();
    uploadSection.style.borderColor = 'var(--primary)';
    uploadSection.style.background = 'rgba(37, 99, 235, 0.05)';
});

uploadSection.addEventListener('dragleave', function(e) {
    e.preventDefault();
    uploadSection.style.borderColor = '';
    uploadSection.style.background = '';
});

uploadSection.addEventListener('drop', function(e) {
    e.preventDefault();
    uploadSection.style.borderColor = '';
    uploadSection.style.background = '';
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        selectedFile = file;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('preview-image').src = e.target.result;
            document.getElementById('preview-section').classList.add('visible');
            document.getElementById('results-section').classList.remove('visible');
        };
        reader.readAsDataURL(file);
    } else {
        alert('Please drop a valid image file');
    }
});

// Analyze image function
window.analyzeImage = async function() {
    if (!selectedFile) {
        alert('Please select an image first');
        return;
    }
    
    // Show loading overlay
    document.getElementById('loading-overlay').classList.add('visible');
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('image', selectedFile);
        
        // Send request to backend
        const response = await fetch('/detect_image', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayResults(data);
        } else {
            throw new Error(data.error || 'Failed to analyze image');
        }
        
    } catch (error) {
        console.error('Error analyzing image:', error);
        alert('Error analyzing image: ' + error.message);
    } finally {
        // Hide loading overlay
        document.getElementById('loading-overlay').classList.remove('visible');
    }
};

// Display results function
function displayResults(data) {
    // Show results section
    document.getElementById('results-section').classList.add('visible');
    
    // Scroll to results
    document.getElementById('results-section').scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });
    
    // Display status badge
    const statusBadge = document.getElementById('status-badge');
    const isAI = data.is_ai_generated;
    const statusClass = isAI ? 'ai-generated' : 'real';
    const icon = isAI ? 'fa-robot' : 'fa-check-circle';
    
    statusBadge.className = `status-badge ${statusClass}`;
    statusBadge.innerHTML = `
        <i class="fas ${icon}"></i>
        ${data.status}
    `;
    
    // Display confidence score
    const confidence = data.confidence;
    document.getElementById('confidence-value').textContent = confidence + '%';
    
    // Animate confidence bar
    setTimeout(() => {
        document.getElementById('confidence-fill').style.width = confidence + '%';
    }, 100);
    
    // Display reasons
    const reasonsList = document.getElementById('reasons-list');
    reasonsList.innerHTML = '';
    
    if (data.reasons && data.reasons.length > 0) {
        data.reasons.forEach(reason => {
            const li = document.createElement('li');
            li.innerHTML = `
                <i class="fas fa-lightbulb"></i>
                <span>${reason}</span>
            `;
            reasonsList.appendChild(li);
        });
    } else {
        reasonsList.innerHTML = '<li><i class="fas fa-info-circle"></i><span>No specific reasons available</span></li>';
    }
    
    // Display artifacts
    const artifactsList = document.getElementById('artifacts-list');
    artifactsList.innerHTML = '';
    
    if (data.artifacts && data.artifacts.length > 0) {
        data.artifacts.forEach(artifact => {
            const artifactDiv = document.createElement('div');
            artifactDiv.className = 'artifact-item';
            artifactDiv.innerHTML = `
                <div class="artifact-header">
                    <span class="artifact-type">${artifact.type}</span>
                    <span class="artifact-confidence">${artifact.confidence}</span>
                </div>
                <div style="color: var(--text-secondary); font-size: 0.9rem;">
                    ${artifact.description}
                </div>
            `;
            artifactsList.appendChild(artifactDiv);
        });
        document.getElementById('artifacts-card').style.display = 'block';
    } else {
        artifactsList.innerHTML = '<p style="color: var(--text-secondary);">No specific artifacts detected</p>';
        document.getElementById('artifacts-card').style.display = 'block';
    }
    
    // Display note if available
    if (data.note) {
        const noteDiv = document.createElement('div');
        noteDiv.style.cssText = 'margin-top: 1rem; padding: 1rem; background: rgba(245, 158, 11, 0.1); border-radius: 8px; color: var(--warning); font-size: 0.9rem;';
        noteDiv.innerHTML = `<i class="fas fa-info-circle"></i> ${data.note}`;
        document.getElementById('results-section').appendChild(noteDiv);
    }
}
