
package com.patientR.repo;

import com.patientR.entity.Professional;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ProfessionalRepository
        extends JpaRepository<Professional, Long> {

    Optional<Professional> findByEmail(String email);

    boolean existsByEmail(String email);
}
