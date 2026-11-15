
package com.patientR.controller;

import com.patientR.entity.CaregiverTask;
import com.patientR.service.CaregiverTaskService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/caregiver-tasks")
@CrossOrigin(origins = "http://localhost:5173")
public class CaregiverTaskController {

    private final CaregiverTaskService taskService;

    public CaregiverTaskController(CaregiverTaskService taskService) {
        this.taskService = taskService;
    }

    @PostMapping("/{patientId}")
    public CaregiverTask createTask(
            @PathVariable Long patientId,
            @RequestBody TaskRequest request) {

        return taskService.createTask(
                patientId,
                request.getTaskDescription()
        );
    }

    @GetMapping("/{patientId}")
    public List<CaregiverTask> getTasks(
            @PathVariable Long patientId) {

        return taskService.getTasks(patientId);
    }

    @PatchMapping("/{taskId}/status")
    public CaregiverTask updateStatus(
            @PathVariable Long taskId,
            @RequestBody StatusRequest request) {

        return taskService.updateStatus(
                taskId,
                request.getStatus()
        );
    }

    public static class TaskRequest {
        private String taskDescription;

        public String getTaskDescription() {
            return taskDescription;
        }

        public void setTaskDescription(String taskDescription) {
            this.taskDescription = taskDescription;
        }
    }

    public static class StatusRequest {
        private String status;

        public String getStatus() {
            return status;
        }

        public void setStatus(String status) {
            this.status = status;
        }
    }
}
