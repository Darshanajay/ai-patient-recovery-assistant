
package com.patientR.controller;

import com.patientR.entity.PdfHistory;
import com.patientR.service.PdfHistoryService;
import com.patientR.service.FileStorageService;

import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@RestController
@RequestMapping("/api/pdf-history")
@CrossOrigin(origins = "http://localhost:5173")
public class PdfHistoryController {

    private final PdfHistoryService historyService;
    private final FileStorageService fileStorageService;

    public PdfHistoryController(
            PdfHistoryService historyService,
            FileStorageService fileStorageService) {
        this.historyService = historyService;
        this.fileStorageService = fileStorageService;
    }

    @GetMapping("/{patientId}")
    public List<PdfHistory> getHistory(@PathVariable Long patientId) {
        return historyService.getHistory(patientId);
    }

    @PostMapping("/upload/{patientId}")
    public PdfHistory uploadPdf(
            @PathVariable Long patientId,
            @RequestParam("file") MultipartFile file) throws IOException {

        String originalName = file.getOriginalFilename();
        String storedName = fileStorageService.saveFile(file);

        return historyService.saveHistory(
                patientId,
                originalName,
                storedName,
                "ANALYZED"
        );
    }

    @GetMapping("/view/{id}")
    public ResponseEntity<Resource> viewPdf(@PathVariable Long id) throws IOException {

        PdfHistory history = historyService.getHistoryRecord(id);
        Resource resource = fileStorageService.loadFile(history.getStoredFileName());

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_PDF)
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline")
                .body(resource);
    }

    @GetMapping("/download/{id}")
    public ResponseEntity<Resource> downloadPdf(@PathVariable Long id) throws IOException {

        PdfHistory history = historyService.getHistoryRecord(id);
        Resource resource = fileStorageService.loadFile(history.getStoredFileName());

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_PDF)
                .header(
                        HttpHeaders.CONTENT_DISPOSITION,
                        "attachment; filename=\"" + history.getOriginalFileName() + "\""
                )
                .body(resource);
    }
}
