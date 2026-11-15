
package com.patientR.repo;

import com.patientR.entity.CaregiverTask;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CaregiverTaskRepository
        extends JpaRepository<CaregiverTask, Long> {

    List<CaregiverTask> findByPatientId(Long patientId);
}
