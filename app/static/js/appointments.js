// Appointments management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize appointment calendar
    initAppointmentCalendar();
    
    // Add event listeners for appointment actions
    setupAppointmentActions();
});

function initAppointmentCalendar() {
    const calendarEl = document.getElementById('appointment-calendar');
    
    if (!calendarEl) return;
    
    // Get doctor ID from data attribute if available
    const doctorId = calendarEl.dataset.doctorId || '';
    
    // Fetch available slots from the server
    fetch(`/api/appointments/availability?doctor_id=${doctorId}`)
        .then(response => response.json())
        .then(data => {
            // Create events array for the calendar
            const events = [];
            
            data.forEach(slot => {
                // Determine color based on availability status
                let color;
                switch(slot.status) {
                    case 'Available':
                        color = '#28a745'; // Green
                        break;
                    case 'Booked':
                        color = '#ffc107'; // Yellow
                        break;
                    case 'Unavailable':
                        color = '#dc3545'; // Red
                        break;
                    default:
                        color = '#6c757d'; // Grey
                }
                
                events.push({
                    id: slot.id,
                    title: slot.status,
                    start: `${slot.date}T${slot.start_time}`,
                    end: `${slot.date}T${slot.end_time}`,
                    color: color,
                    extendedProps: {
                        status: slot.status,
                        doctorId: slot.doctor_id,
                        appointmentId: slot.appointment_id || null
                    }
                });
            });
            
            // Initialize the calendar
            const calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'timeGridWeek',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'timeGridWeek,timeGridDay'
                },
                slotDuration: '00:05:00', // 5-minute slots
                slotLabelInterval: '00:30:00', // 30-minute labels
                allDaySlot: false,
                events: events,
                eventClick: function(info) {
                    handleSlotClick(info.event);
                }
            });
            
            calendar.render();
        })
        .catch(error => {
            console.error('Error loading appointment data:', error);
            showNotification('Error loading appointment data. Please try again.', 'error');
        });
}

function handleSlotClick(event) {
    const status = event.extendedProps.status;
    const slotId = event.id;
    const doctorId = event.extendedProps.doctorId;
    const appointmentId = event.extendedProps.appointmentId;
    
    // Different actions based on slot status and user role
    const userRole = document.body.dataset.userRole || '';
    
    if (userRole === 'student') {
        if (status === 'Available') {
            // Show booking modal for available slots
            showBookingModal(slotId, doctorId);
        } else if (status === 'Booked' && appointmentId) {
            // Check if this is the student's own appointment
            fetch(`/api/appointments/${appointmentId}/is-owner`)
                .then(response => response.json())
                .then(data => {
                    if (data.is_owner) {
                        // Show cancel confirmation for own appointments
                        showCancelConfirmation(appointmentId);
                    } else {
                        showNotification('This slot is already booked.', 'info');
                    }
                })
                .catch(error => {
                    console.error('Error checking appointment ownership:', error);
                });
        } else {
            showNotification('This slot is not available for booking.', 'info');
        }
    } else if (userRole === 'doctor') {
        if (status === 'Booked' && appointmentId) {
            // Show appointment details for doctors
            showAppointmentDetails(appointmentId);
        } else if (status === 'Available') {
            // Allow doctors to mark slots as unavailable
            showUnavailableConfirmation(slotId, doctorId);
        }
    } else if (userRole === 'staff') {
        if (status === 'Booked' && appointmentId) {
            // Show appointment details for staff
            showAppointmentDetails(appointmentId);
        }
    }
}

function showBookingModal(slotId, doctorId) {
    // Get the booking modal
    const modal = document.getElementById('booking-modal');
    const form = document.getElementById('booking-form');
    
    if (!modal || !form) return;
    
    // Set form values
    form.elements['slot_id'].value = slotId;
    form.elements['doctor_id'].value = doctorId;
    
    // Show the modal
    modal.style.display = 'block';
    
    // Close modal when clicking the close button
    const closeBtn = modal.querySelector('.close');
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    };
    
    // Close modal when clicking outside the modal content
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
    
    // Handle form submission
    form.onsubmit = function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        
        fetch('/api/appointments/book', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Appointment booked successfully!', 'success');
                modal.style.display = 'none';
                
                // Refresh the calendar
                setTimeout(() => {
                    initAppointmentCalendar();
                }, 1000);
            } else {
                showNotification(data.message || 'Failed to book appointment.', 'error');
            }
        })
        .catch(error => {
            console.error('Error booking appointment:', error);
            showNotification('Error booking appointment. Please try again.', 'error');
        });
    };
}

function showCancelConfirmation(appointmentId) {
    if (confirm('Are you sure you want to cancel this appointment?')) {
        fetch(`/api/appointments/${appointmentId}/cancel`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Appointment cancelled successfully!', 'success');
                
                // Refresh the calendar
                setTimeout(() => {
                    initAppointmentCalendar();
                }, 1000);
            } else {
                showNotification(data.message || 'Failed to cancel appointment.', 'error');
            }
        })
        .catch(error => {
            console.error('Error cancelling appointment:', error);
            showNotification('Error cancelling appointment. Please try again.', 'error');
        });
    }
}

function showUnavailableConfirmation(slotId, doctorId) {
    if (confirm('Are you sure you want to mark this slot as unavailable?')) {
        fetch(`/api/appointments/availability/${slotId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'Unavailable',
                doctor_id: doctorId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Slot marked as unavailable successfully!', 'success');
                
                // Refresh the calendar
                setTimeout(() => {
                    initAppointmentCalendar();
                }, 1000);
            } else {
                showNotification(data.message || 'Failed to update slot.', 'error');
            }
        })
        .catch(error => {
            console.error('Error updating slot:', error);
            showNotification('Error updating slot. Please try again.', 'error');
        });
    }
}

function showAppointmentDetails(appointmentId) {
    // Fetch appointment details
    fetch(`/api/appointments/${appointmentId}`)
        .then(response => response.json())
        .then(data => {
            if (data.appointment) {
                const appointment = data.appointment;
                
                // Create modal content
                let modalContent = `
                    <div class="appointment-details">
                        <h3>Appointment Details</h3>
                        <p><strong>Student:</strong> ${appointment.StudentFirstName} ${appointment.StudentLastName}</p>
                        <p><strong>Date:</strong> ${appointment.AppointmentDate}</p>
                        <p><strong>Time:</strong> ${appointment.AppointmentTime}</p>
                        <p><strong>Status:</strong> ${appointment.Status}</p>
                    </div>
                `;
                
                // Add actions based on user role
                const userRole = document.body.dataset.userRole || '';
                
                if (userRole === 'doctor') {
                    modalContent += `
                        <div class="appointment-actions">
                            <button class="btn btn-success" onclick="completeAppointment(${appointmentId})">Complete</button>
                            <button class="btn btn-warning" onclick="rescheduleAppointment(${appointmentId})">Reschedule</button>
                            <button class="btn btn-danger" onclick="cancelAppointment(${appointmentId})">Cancel</button>
                        </div>
                        <div class="prescription-form">
                            <h4>Add Prescription</h4>
                            <form id="prescription-form">
                                <input type="hidden" name="appointment_id" value="${appointmentId}">
                                <div class="form-group">
                                    <label for="medication">Medication</label>
                                    <select name="medication_id" id="medication" class="form-control" required>
                                        <option value="">Select Medication</option>
                                        <!-- Will be populated via AJAX -->
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="quantity">Quantity</label>
                                    <input type="number" name="quantity" id="quantity" class="form-control" min="1" required>
                                </div>
                                <div class="form-group">
                                    <label for="instructions">Instructions</label>
                                    <textarea name="instructions" id="instructions" class="form-control" rows="3" required></textarea>
                                </div>
                                <button type="submit" class="btn btn-primary">Add Prescription</button>
                            </form>
                        </div>
                    `;
                    
                    // Load medications for the dropdown
                    loadMedications();
                }
                
                // Display the modal
                const modalElement = document.getElementById('appointment-details-modal');
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
                    
                    // Handle prescription form submission
                    const prescriptionForm = document.getElementById('prescription-form');
                    if (prescriptionForm) {
                        prescriptionForm.onsubmit = function(e) {
                            e.preventDefault();
                            addPrescription(prescriptionForm);
                        };
                    }
                } else {
                    showNotification('Modal element not found.', 'error');
                }
            } else {
                showNotification('Failed to load appointment details.', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading appointment details:', error);
            showNotification('Error loading appointment details. Please try again.', 'error');
        });
}

function loadMedications() {
    fetch('/api/medications')
        .then(response => response.json())
        .then(data => {
            const medicationSelect = document.getElementById('medication');
            
            if (medicationSelect && data.medications) {
                data.medications.forEach(med => {
                    const option = document.createElement('option');
                    option.value = med.MedicationID;
                    option.textContent = `${med.Name} (${med.DosageForm})`;
                    medicationSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading medications:', error);
        });
}

function addPrescription(form) {
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
        } else {
            showNotification(data.message || 'Failed to add prescription.', 'error');
        }
    })
    .catch(error => {
        console.error('Error adding prescription:', error);
        showNotification('Error adding prescription. Please try again.', 'error');
    });
}

function completeAppointment(appointmentId) {
    fetch(`/api/appointments/${appointmentId}/complete`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Appointment marked as completed!', 'success');
            
            // Close modal
            const modalElement = document.getElementById('appointment-details-modal');
            if (modalElement) {
                modalElement.style.display = 'none';
            }
            
            // Refresh the calendar
            setTimeout(() => {
                initAppointmentCalendar();
            }, 1000);
        } else {
            showNotification(data.message || 'Failed to complete appointment.', 'error');
        }
    })
    .catch(error => {
        console.error('Error completing appointment:', error);
        showNotification('Error completing appointment. Please try again.', 'error');
    });
}

function rescheduleAppointment(appointmentId) {
    // Show reschedule form
    const modalElement = document.getElementById('appointment-details-modal');
    if (modalElement) {
        const modalBody = modalElement.querySelector('.modal-body');
        
        modalBody.innerHTML = `
            <div class="reschedule-form">
                <h3>Reschedule Appointment</h3>
                <form id="reschedule-form">
                    <input type="hidden" name="appointment_id" value="${appointmentId}">
                    <div class="form-group">
                        <label for="new-date">New Date</label>
                        <input type="date" name="new_date" id="new-date" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label for="new-time">New Time</label>
                        <input type="time" name="new_time" id="new-time" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Reschedule</button>
                    <button type="button" class="btn btn-secondary" onclick="showAppointmentDetails(${appointmentId})">Cancel</button>
                </form>
            </div>
        `;
        
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('new-date').min = today;
        
        // Handle form submission
        const rescheduleForm = document.getElementById('reschedule-form');
        rescheduleForm.onsubmit = function(e) {
            e.preventDefault();
            
            const formData = new FormData(rescheduleForm);
            
            fetch('/api/appointments/reschedule', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Appointment rescheduled successfully!', 'success');
                    
                    // Close modal
                    modalElement.style.display = 'none';
                    
                    // Refresh the calendar
                    setTimeout(() => {
                        initAppointmentCalendar();
                    }, 1000);
                } else {
                    showNotification(data.message || 'Failed to reschedule appointment.', 'error');
                }
            })
            .catch(error => {
                console.error('Error rescheduling appointment:', error);
                showNotification('Error rescheduling appointment. Please try again.', 'error');
            });
        };
    }
}

function cancelAppointment(appointmentId) {
    if (confirm('Are you sure you want to cancel this appointment?')) {
        fetch(`/api/appointments/${appointmentId}/cancel`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Appointment cancelled successfully!', 'success');
                
                // Close modal
                const modalElement = document.getElementById('appointment-details-modal');
                if (modalElement) {
                    modalElement.style.display = 'none';
                }
                
                // Refresh the calendar
                setTimeout(() => {
                    initAppointmentCalendar();
                }, 1000);
            } else {
                showNotification(data.message || 'Failed to cancel appointment.', 'error');
            }
        })
        .catch(error => {
            console.error('Error cancelling appointment:', error);
            showNotification('Error cancelling appointment. Please try again.', 'error');
        });
    }
}

function setupAppointmentActions() {
    // Add event listeners for appointment-related buttons
    document.addEventListener('click', function(event) {
        // Check if the clicked element is a button with a specific class or ID
        if (event.target.matches('.book-appointment-btn')) {
            const doctorId = event.target.dataset.doctorId;
            const date = event.target.dataset.date;
            
            // Show available slots for the selected doctor and date
            showAvailableSlots(doctorId, date);
        }
    });
}

function showAvailableSlots(doctorId, date) {
    fetch(`/api/appointments/availability?doctor_id=${doctorId}&date=${date}`)
        .then(response => response.json())
        .then(data => {
            const slotsContainer = document.getElementById('available-slots');
            
            if (slotsContainer && data.slots) {
                // Clear previous slots
                slotsContainer.innerHTML = '';
                
                if (data.slots.length === 0) {
                    slotsContainer.innerHTML = '<p>No available slots for this date.</p>';
                    return;
                }
                
                // Create slots display
                const slotsGrid = document.createElement('div');
                slotsGrid.className = 'slots-grid';
                
                data.slots.forEach(slot => {
                    const slotElement = document.createElement('div');
                    slotElement.className = `slot ${slot.status.toLowerCase()}`;
                    slotElement.textContent = slot.time;
                    
                    if (slot.status === 'Available') {
                        slotElement.addEventListener('click', function() {
                            bookSlot(doctorId, date, slot.time);
                        });
                    }
                    
                    slotsGrid.appendChild(slotElement);
                });
                
                slotsContainer.appendChild(slotsGrid);
            }
        })
        .catch(error => {
            console.error('Error loading available slots:', error);
            showNotification('Error loading available slots. Please try again.', 'error');
        });
}

function bookSlot(doctorId, date, time) {
    // Show booking form modal
    const modalElement = document.getElementById('booking-modal');
    if (modalElement) {
        const form = document.getElementById('booking-form');
        
        // Set form values
        form.elements['doctor_id'].value = doctorId;
        form.elements['appointment_date'].value = date;
        form.elements['appointment_time'].value = time;
        
        // Show the modal
        modalElement.style.display = 'block';
    }
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
