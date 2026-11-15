
package com.patientR.config;

import com.patientR.entity.Professional;
import com.patientR.repo.ProfessionalRepository;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
public class ProfessionalAccountInitializer {

    @Value("${app.bootstrap-professional.name:}")
    private String professionalName;

    @Value("${app.bootstrap-professional.email:}")
    private String professionalEmail;

    @Value("${app.bootstrap-professional.password:}")
    private String professionalPassword;

    @Bean
    public CommandLineRunner initializeProfessional(
            ProfessionalRepository repository,
            PasswordEncoder passwordEncoder) {

        return args -> {
            System.out.println("Name configured: " + !professionalName.isBlank());
            System.out.println("Email configured: " + !professionalEmail.isBlank());
            System.out.println("Password configured: " + !professionalPassword.isBlank());

            // Skip initialization when credentials are not configured.
            if (professionalName.isBlank()
                    || professionalEmail.isBlank()
                    || professionalPassword.isBlank()) {
                System.out.println(
                        "Professional account initialization skipped.");
                return;
            }

            if (repository.existsByEmail(professionalEmail)) {
                System.out.println(
                        "Professional account already exists.");
                return;
            }

            Professional professional = new Professional();

            professional.setFullName(professionalName);
            professional.setEmail(professionalEmail);
            professional.setPassword(
                    passwordEncoder.encode(professionalPassword)
            );
            professional.setRole("PROFESSIONAL");
            professional.setActive(true);

            repository.save(professional);

            System.out.println(
                    "Initial professional account created.");
        };
    }
}
