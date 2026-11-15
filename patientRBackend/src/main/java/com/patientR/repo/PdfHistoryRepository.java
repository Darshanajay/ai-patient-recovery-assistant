
package com.patientR.repo;

import com.patientR.entity.PdfHistory;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PdfHistoryRepository
        extends JpaRepository<PdfHistory, Long> {

    List<PdfHistory> findByPatientIdOrderByUploadedAtDesc(Long patientId);
}
