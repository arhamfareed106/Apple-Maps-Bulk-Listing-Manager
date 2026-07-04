// Global variables
let currentJobId = null;

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('file');
const dropZone = document.getElementById('dropZone');
const fileNameDisplay = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');
const aggregatorSelect = document.getElementById('aggregator');
const mappingSection = document.getElementById('mappingSection');
const columnMappingDiv = document.getElementById('columnMapping');
const previewSection = document.getElementById('previewSection');
const previewTable = document.getElementById('previewTable');

// Upload Page Functions
document.addEventListener('DOMContentLoaded', function() {
    // Set up drag and drop
    setupDragAndDrop();
    
    // Set up form submission
    setupFormSubmission();
    
    // Set up file input change
    fileInput.addEventListener('change', handleFileSelect);
});

function setupDragAndDrop() {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropZone.classList.add('drag-over');
    }

    function unhighlight() {
        dropZone.classList.remove('drag-over');
    }

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        
        // Display file name
        fileNameDisplay.textContent = file.name;
        fileNameDisplay.classList.remove('hidden');
        
        // Enable upload button
        uploadBtn.disabled = false;
        
        // Show preview section
        previewSection.classList.remove('hidden');
        
        // Show mapping section
        mappingSection.classList.remove('hidden');
        
        // Show preview of file data
        showFilePreview(file);
        
        // Show column mapping options
        showColumnMappingOptions(file);
    }
}

function showFilePreview(file) {
    // For demo purposes, we'll show a sample preview
    // In a real implementation, this would read the file content
    previewTable.innerHTML = `
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Business Name</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Address</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">City</th>
                    <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">State</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Sample Store 1</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">123 Main St</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">New York</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">NY</td>
                </tr>
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Sample Store 2</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">456 Oak Ave</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Los Angeles</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">CA</td>
                </tr>
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Sample Store 3</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">789 Pine Rd</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Chicago</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">IL</td>
                </tr>
            </tbody>
        </table>
    `;
}

function showColumnMappingOptions(file) {
    // For demo purposes, show sample mapping options
    columnMappingDiv.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Business Name</label>
                <select class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                    <option value="">Select column...</option>
                    <option value="name">Name</option>
                    <option value="business_name">Business Name</option>
                    <option value="company">Company</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <select class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                    <option value="">Select column...</option>
                    <option value="address">Address</option>
                    <option value="street">Street</option>
                    <option value="street_address">Street Address</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">City</label>
                <select class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                    <option value="">Select column...</option>
                    <option value="city">City</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">State</label>
                <select class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                    <option value="">Select column...</option>
                    <option value="state">State</option>
                    <option value="province">Province</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">ZIP/Postal Code</label>
                <select class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                    <option value="">Select column...</option>
                    <option value="zip">ZIP</option>
                    <option value="postal_code">Postal Code</option>
                    <option value="postcode">Postcode</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <select class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                    <option value="">Select column...</option>
                    <option value="phone">Phone</option>
                    <option value="phone_number">Phone Number</option>
                    <option value="tel">Tel</option>
                </select>
            </div>
        </div>
    `;
}

function setupFormSubmission() {
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData();
            const file = fileInput.files[0];
            const aggregator = aggregatorSelect.value;
            
            if (!file) {
                alert('Please select a file to upload');
                return;
            }
            
            formData.append('file', file);
            formData.append('aggregator', aggregator);
            
            // Disable button and show loading state
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Uploading...';
            
            // Submit the form
            submitUpload(formData);
        });
    }
}

function submitUpload(formData) {
    // In a real implementation, this would make an API call
    // For demo purposes, we'll simulate the upload
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Redirect to progress page
        window.location.href = data.redirect_url;
    })
    .catch(error => {
        console.error('Upload error:', error);
        alert('Upload failed. Please try again.');
        
        // Re-enable button
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fas fa-upload mr-2"></i> Start Upload';
    });
}

// Progress Page Functions
function initProgressPage() {
    const jobId = document.getElementById('jobId')?.textContent;
    if (jobId) {
        currentJobId = jobId;
        startProgressTracking(jobId);
    }
    
    // Set up cancel button
    const cancelBtn = document.getElementById('cancelBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelJob);
    }
}

function startProgressTracking(jobId) {
    // In a real implementation, this would connect to SSE
    // For demo purposes, we'll simulate progress
    
    // Simulate progress updates
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.floor(Math.random() * 10) + 5;
        if (progress > 100) progress = 100;
        
        updateProgress(progress);
        
        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                // Redirect to reports page when complete
                window.location.href = '/reports';
            }, 2000);
        }
    }, 1000);
}

function updateProgress(progress) {
    const progressBar = document.getElementById('progressBar');
    const percentage = document.getElementById('percentage');
    const statusText = document.getElementById('statusText');
    const successCount = document.getElementById('successCount');
    const failedCount = document.getElementById('failedCount');
    const totalCount = document.getElementById('totalCount');
    
    // Update progress bar
    progressBar.style.width = `${progress}%`;
    percentage.textContent = `${progress}%`;
    
    // Update status
    if (progress < 100) {
        statusText.textContent = 'Processing';
        statusText.className = 'font-medium text-yellow-600';
    } else {
        statusText.textContent = 'Completed';
        statusText.className = 'font-medium text-green-600';
    }
    
    // Update counts (simulated)
    const success = Math.floor(progress * 0.9);
    const failed = Math.floor(progress * 0.1);
    const total = success + failed;
    
    successCount.textContent = success;
    failedCount.textContent = failed;
    totalCount.textContent = total;
    
    // Add to activity log
    addToActivityLog(`Processed ${total} locations (${success} successful, ${failed} failed)`);
}

function addToActivityLog(message) {
    const activityLog = document.getElementById('activityLog');
    const now = new Date().toLocaleTimeString();
    
    const li = document.createElement('li');
    li.className = 'px-4 py-4 sm:px-6';
    li.innerHTML = `
        <div class="flex items-center">
            <div class="flex-shrink-0 h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                <i class="fas fa-sync text-blue-600 text-xs"></i>
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium text-gray-900">${message}</p>
                <p class="text-sm text-gray-500">${now}</p>
            </div>
        </div>
    `;
    
    // Add to top of list
    if (activityLog.firstChild) {
        activityLog.insertBefore(li, activityLog.firstChild);
    } else {
        activityLog.appendChild(li);
    }
}

function cancelJob() {
    if (confirm('Are you sure you want to cancel this upload?')) {
        // In a real implementation, this would call the API to cancel the job
        alert('Upload cancelled');
        window.location.href = '/';
    }
}

// Initialize page-specific functions
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the progress page
    if (window.location.pathname.includes('/progress')) {
        initProgressPage();
    }
});