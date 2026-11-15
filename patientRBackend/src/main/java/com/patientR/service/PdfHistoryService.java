
package com.patientR.service;

import com.patientR.entity.PdfHistory;
import com.patientR.entity.Patient;
import com.patientR.repo.PdfHistoryRepository;
import com.patientR.repo.PatientRepository;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class PdfHistoryService {

    private final PdfHistoryRepository historyRepository;
    private final PatientRepository patientRepository;

    public PdfHistoryService(
            PdfHistoryRepository historyRepository,
            PatientRepository patientRepository) {
        this.historyRepository = historyRepository;
        this.patientRepository = patientRepository;
    }

    public PdfHistory saveHistory(
            Long patientId,
            String originalFileName,
            String storedFileName,
            String status) {

        Patient patient = patientRepository.findById(patientId)
                .orElseThrow(() -> new RuntimeException("Patient not found"));

        PdfHistory history = new PdfHistory();
        history.setPatient(patient);
        history.setOriginalFileName(originalFileName);
        history.setStoredFileName(storedFileName);
        history.setAnalysisStatus(status);

        return historyRepository.save(history);
    }

    public List<PdfHistory> getHistory(Long patientId) {
        return historyRepository.findByPatientIdOrderByUploadedAtDesc(patientId);
    }

    public PdfHistory getHistoryRecord(Long id) {
        return historyRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("PDF history record not found"));
    }
}
