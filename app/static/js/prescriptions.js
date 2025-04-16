// Prescriptions management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize prescriptions table
    initPrescriptionsTable();
    
    // Setup prescription form
    setupPrescriptionForm();
    
    // Setup medicine dispensing
    setupMedicineDispensing();
});

function initPrescriptionsTable() {
    const table = document.getElementById('prescriptions-table');
    
    if (!table) return;
    
    // Check if DataTables is available
    if (typeof $.fn.DataTable !== 'undefined') {
        $(table).DataTable({
            responsive: true,
            order: [[0, 'desc']], // Sort by first column (date) descending
            language: {
                search: "Search prescriptions:",
                lengthMenu: "Show _MENU_ prescriptions per page",
                info: "Showing _START_ to _END_ of _TOTAL_ prescriptions",
                emptyTable: "No prescriptions available"
            }
        });
    }
}

function setupPrescriptionForm() {
    const form = document.getElementById('prescription-form');
    
    if (!form) return;
    
    // Load medications for the dropdown
    loadMedications();
    
    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        
        fetch('/api/prescriptions/add', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Prescription added successfully!', 'success');
                form.reset();
                
                // Reload prescriptions table if it exists
                if (document.getElementById('prescriptions-table')) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
            } else {
                showNotification(data.message || 'Failed to add prescription.', 'error');
            }
        })
        .catch(error => {
            console.error('Error adding prescription:', error);
            showNotification('Error adding prescription. Please try again.', 'error');
        });
    });
}
function loadMedications() {
    const medicationSelect = document.getElementById('medication');
    
    if (!medicationSelect) return;
    
    fetch('/api/medications')
        .then(response => response.json())
        .then(data => {
            if (data.medications) {
                // Clear existing options
                medicationSelect.innerHTML = '<option value="">Select Medication</option>';
                
                // Add medications to dropdown
                data.medications.forEach(med => {
                    const option = document.createElement('option');
                    option.value = med.MedicationID;
                    option.textContent = `${med.Name} (${med.DosageForm}) - Stock: ${med.QuantityInStock}`;
                    
                    // Disable option if out of stock
                    if (med.QuantityInStock <= 0) {
                        option.disabled = true;
                        option.textContent += ' (Out of Stock)';
                    }
                    
                    medicationSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading medications:', error);
        });
}

function setupMedicineDispensing() {
    // Add event listeners to dispense buttons
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('dispense-btn')) {
            const prescriptionId = event.target.dataset.prescriptionId;
            const medicationId = event.target.dataset.medicationId;
            
            showDispenseForm(prescriptionId, medicationId);
        }
    });
}

function showDispenseForm(prescriptionId, medicationId) {
    // Get prescription details
    fetch(`/api/prescriptions/${prescriptionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.prescription) {
                const prescription = data.prescription;
                
                // Create modal content
                const modalContent = `
                    <div class="dispense-form">
                        <h3>Dispense Medication</h3>
                        <p><strong>Student:</strong> ${prescription.StudentFirstName} ${prescription.StudentLastName}</p>
                        <p><strong>Medication:</strong> ${prescription.MedicationName} (${prescription.DosageForm})</p>
                        <p><strong>Prescribed Quantity:</strong> ${prescription.Quantity}</p>
                        <p><strong>Instructions:</strong> ${prescription.Instructions}</p>
                        <form id="dispense-form">
                            <input type="hidden" name="prescription_id" value="${prescriptionId}">
                            <input type="hidden" name="medication_id" value="${medicationId}">
                            <div class="form-group">
                                <label for="quantity-given">Quantity to Dispense</label>
                                <input type="number" name="quantity_given" id="quantity-given" class="form-control" min="1" max="${prescription.Quantity}" value="${prescription.Quantity}" required>
                            </div>
                            <button type="submit" class="btn btn-primary">Dispense</button>
                        </form>
                    </div>
                `;
                
                // Display the modal
                const modalElement = document.getElementById('dispense-modal');
                if (modalElement) {
                    modalElement.querySelector('.modal-body').innerHTML = modalContent;
                    modalElement.style.display = 'block';
                    
                    // Close modal when clicking the close button
                    const closeBtn = modalElement.querySelector('.close');
                    closeBtn.onclick = function() {
                        modalElement.style.display = 'none';
                    };
                    
                    // Close modal when clicking outside the modal content
                    window.onclick = function(event) {
                        if (event.target === modalElement) {
                            modalElement.style.display = 'none';
                        }
                    };
                    
                    // Handle form submission
                    const dispenseForm = document.getElementById('dispense-form');
                    if (dispenseForm) {
                        dispenseForm.onsubmit = function(e) {
                            e.preventDefault();
                            dispenseMedication(dispenseForm);
                        };
                    }
                } else {
                    showNotification('Modal element not found.', 'error');
                }
            } else {
                showNotification('Failed to load prescription details.', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading prescription details:', error);
            showNotification('Error loading prescription details. Please try again.', 'error');
        });
}

function dispenseMedication(form) {
    const formData = new FormData(form);
    
    fetch('/api/medicines/dispense', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Medication dispensed successfully!', 'success');
            
            // Close modal
            const modalElement = document.getElementById('dispense-modal');
            if (modalElement) {
                modalElement.style.display = 'none';
            }
            
            // Reload prescriptions table
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification(data.message || 'Failed to dispense medication.', 'error');
        }
    })
    .catch(error => {
        console.error('Error dispensing medication:', error);
        showNotification('Error dispensing medication. Please try again.', 'error');
    });
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500);
    }, 3000);
}
