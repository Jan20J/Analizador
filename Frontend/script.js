// script.js
document.addEventListener('DOMContentLoaded', () => {
    // Referencias a los elementos del DOM
    const imageInput = document.getElementById('image-input');
    const preview1 = document.getElementById('preview1');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultsArea = document.getElementById('results-area');
    const analysisImageEl = document.getElementById('analysis-image');
    const loader = document.getElementById('loader');

    let file = null;

    // Función para mostrar la vista previa de la imagen
    const showPreview = (input, previewElement) => {
        const selectedFile = input.files[0];
        if (selectedFile) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewElement.src = e.target.result;
                previewElement.classList.add('has-image');
            };
            reader.readAsDataURL(selectedFile);
            return selectedFile;
        }
        return null;
    };

    // Event Listener para el input de archivo
    imageInput.addEventListener('change', () => {
        file = showPreview(imageInput, preview1);
        validateInputs();
    });

    // Habilitar o deshabilitar el botón de analizar
    const validateInputs = () => {
        analyzeBtn.disabled = !file;
    };
    
    // Función principal para analizar la imagen
    const handleAnalyze = async () => {
        if (!file) {
            alert('Por favor, selecciona una imagen para analizar.');
            return;
        }

        loader.hidden = false;
        resultsArea.hidden = true;
        analyzeBtn.disabled = true;

        const formData = new FormData();
        // Cambiamos 'image1' por 'image' para que coincida con el backend
        formData.append('image', file);

        try {
            // Apuntamos al nuevo endpoint y al servidor local
            const response = await fetch('https://analizador-backend-2ubi.onrender.com/analyze', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Error del servidor: ${response.status}`);
            }

            const data = await response.json();

            // Mostrar los resultados
            analysisImageEl.src = data.analysis_image_url;
            resultsArea.hidden = false;

        } catch (error) {
            console.error('Error al analizar la imagen:', error);
            alert(`Ocurrió un error: ${error.message}`);
        } finally {
            loader.hidden = true;
            analyzeBtn.disabled = false;
        }
    };

    analyzeBtn.addEventListener('click', handleAnalyze);
    validateInputs();
});