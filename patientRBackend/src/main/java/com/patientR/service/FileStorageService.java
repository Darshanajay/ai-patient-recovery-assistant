
package com.patientR.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

@Service
public class FileStorageService {

    @Value("${app.upload.dir:uploads}")
    private String uploadDir;

    public String saveFile(MultipartFile file) throws IOException {

        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("Please select a PDF file");
        }

        String originalName = file.getOriginalFilename();

        if (!"application/pdf".equalsIgnoreCase(file.getContentType())
                || originalName == null
                || !originalName.toLowerCase().endsWith(".pdf")) {
            throw new IllegalArgumentException("Only PDF files are allowed");
        }

        if (file.getSize() > 10 * 1024 * 1024) {
            throw new IllegalArgumentException("File size must be below 10 MB");
        }

        Path directory = Paths.get(uploadDir).toAbsolutePath().normalize();

        Files.createDirectories(directory);

        String storedName = UUID.randomUUID() + ".pdf";

        Path destination = directory.resolve(storedName).normalize();

        if (!destination.startsWith(directory)) {
            throw new IOException("Invalid file path");
        }

        Files.copy(file.getInputStream(), destination);

        return storedName;
    }

    public Resource loadFile(String storedFileName) throws IOException {

        if (storedFileName == null
                || !storedFileName.matches("[a-fA-F0-9-]+\\.pdf")) {
            throw new IllegalArgumentException("Invalid PDF filename");
        }

        Path directory = Paths.get(uploadDir).toAbsolutePath().normalize();
        Path filePath = directory.resolve(storedFileName).normalize();

        if (!filePath.startsWith(directory) || !Files.isRegularFile(filePath)) {
            throw new IOException("PDF file not found");
        }

        Resource resource = new UrlResource(filePath.toUri());

        if (!resource.exists() || !resource.isReadable()) {
            throw new IOException("PDF file cannot be read");
        }

        return resource;
    }
}
