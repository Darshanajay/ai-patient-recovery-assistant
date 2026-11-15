
package com.patientR.repo;

import com.patientR.entity.ProfessionalReview;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ProfessionalReviewRepository
        extends JpaRepository<ProfessionalReview, Long> {

    List<ProfessionalReview> findByTaskIdOrderByReviewedAtDesc(Long taskId);

    List<ProfessionalReview> findByProfessionalIdOrderByReviewedAtDesc(
            Long professionalId);
}
