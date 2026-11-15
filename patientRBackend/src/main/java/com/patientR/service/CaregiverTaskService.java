
package com.patientR.service;

import com.patientR.entity.CaregiverTask;
import com.patientR.entity.Patient;
import com.patientR.repo.CaregiverTaskRepository;
import com.patientR.repo.PatientRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CaregiverTaskService {

    private final CaregiverTaskRepository taskRepository;
    private final PatientRepository patientRepository;

    public CaregiverTaskService(
            CaregiverTaskRepository taskRepository,
            PatientRepository patientRepository) {

        this.taskRepository = taskRepository;
        this.patientRepository = patientRepository;
    }

    // Create a new caregiver task
    public CaregiverTask createTask(Long patientId, String description) {

        Patient patient = patientRepository.findById(patientId)
                .orElseThrow(() ->
                        new RuntimeException("Patient not found"));

        CaregiverTask task = new CaregiverTask();

        task.setPatient(patient);
        task.setTaskDescription(description);

        // Caregiver acknowledgement
        task.setStatus("PENDING");

        // Professional verification
        task.setVerificationStatus("REQUIRES_REVIEW");

        return taskRepository.save(task);
    }

    // Get all tasks for a patient
    public List<CaregiverTask> getTasks(Long patientId) {
        return taskRepository.findByPatientId(patientId);
    }

    // Update caregiver acknowledgement status
    public CaregiverTask updateStatus(Long taskId, String status) {

        if (status == null ||
                (!status.equals("PENDING") &&
                        !status.equals("COMPLETED"))) {

            throw new IllegalArgumentException(
                    "Invalid task status");
        }

        CaregiverTask task = taskRepository.findById(taskId)
                .orElseThrow(() ->
                        new RuntimeException("Task not found"));

        task.setStatus(status);

        return taskRepository.save(task);
    }
}
