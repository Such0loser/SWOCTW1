document.getElementById('calculateBtn').addEventListener('click', async () => {
    // 1. Get references to all necessary DOM elements
    const fileInput = document.getElementById('vectorFile');
    const calculateBtn = document.getElementById('calculateBtn'); // Get the button itself
    const file = fileInput.files[0];

    const resultDiv = document.getElementById('result');
    const areaResultSpan = document.getElementById('areaResult');
    const convertedImage = document.getElementById('convertedImage');
    const errorMessage = document.getElementById('errorMessage');
    const loadingMessage = document.getElementById('loadingMessage');

    // 2. Initial UI state reset and loading indicator activation
    resultDiv.style.display = 'none';
    errorMessage.style.display = 'none';
    loadingMessage.style.display = 'block'; // Show loading message
    calculateBtn.disabled = true; // Disable button to prevent multiple submissions
    
    // Clear previous image source and area text
    convertedImage.src = '#'; 
    areaResultSpan.textContent = '';

    // 3. Client-side file validation
    if (!file) {
        errorMessage.textContent = 'الرجاء اختيار ملف AI أو EPS.';
        errorMessage.style.display = 'block';
        loadingMessage.style.display = 'none';
        calculateBtn.disabled = false; // Re-enable button
        return; // Stop execution if no file is selected
    }

    // Basic file type validation (check extension)
    const allowedExtensions = ['.ai', '.eps'];
    const fileName = file.name.toLowerCase();
    const fileExtension = fileName.substring(fileName.lastIndexOf('.'));

    if (!allowedExtensions.includes(fileExtension)) {
        errorMessage.textContent = 'صيغة الملف غير مدعومة. الرجاء اختيار ملف AI أو EPS.';
        errorMessage.style.display = 'block';
        loadingMessage.style.display = 'none';
        calculateBtn.disabled = false; // Re-enable button
        return;
    }

    // 4. Prepare data for server
    const formData = new FormData();
    formData.append('file', file);

    // 5. Send request to backend and handle response
    try {
        const response = await fetch('/calculate_area', {
            method: 'POST',
            body: formData
        });

        // Parse JSON response. Note: response.json() will throw if not valid JSON
        const data = await response.json(); 

        if (response.ok) { // Check if the HTTP status code is in the 200-299 range
            areaResultSpan.textContent = data.area.toFixed(2); // Format to 2 decimal places
            convertedImage.src = 'data:image/jpeg;base64,' + data.image_base64; // Display base64 image
            resultDiv.style.display = 'block'; // Show results section
        } else {
            // Handle server-side errors (e.g., 400, 500 status codes)
            errorMessage.textContent = data.error || 'حدث خطأ غير معروف من الخادم.';
            errorMessage.style.display = 'block';
        }
    } catch (error) {
        // Handle network errors or issues with parsing JSON
        errorMessage.textContent = 'حدث خطأ في الاتصال بالخادم أو معالجة البيانات: ' + error.message;
        errorMessage.style.display = 'block';
    } finally {
        // This block will always execute, regardless of success or failure
        loadingMessage.style.display = 'none'; // Hide loading message
        calculateBtn.disabled = false; // Re-enable the button
    }
});