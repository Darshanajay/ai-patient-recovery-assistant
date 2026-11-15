
package com.patientR.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "professional_reviews")
public class ProfessionalReview {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(optional = false)
    @JoinColumn(name = "task_id", nullable = false)
    private CaregiverTask task;

    @ManyToOne(optional = false)
    @JoinColumn(name = "professional_id", nullable = false)
    private Professional professional;

    @Column(nullable = false)
    private String decision;

    @Column(length = 1000)
    private String comments;

    @Column(nullable = false)
    private LocalDateTime reviewedAt;

    public ProfessionalReview() {
    }

    @PrePersist
    public void onCreate() {
        reviewedAt = LocalDateTime.now();
    }

    public Long getId() {
        return id;
    }

    public CaregiverTask getTask() {
        return task;
    }

    public void setTask(CaregiverTask task) {
        this.task = task;
    }

    public Professional getProfessional() {
        return professional;
    }

    public void setProfessional(Professional professional) {
        this.professional = professional;
    }

    public String getDecision() {
        return decision;
    }

    public void setDecision(String decision) {
        this.decision = decision;
    }

    public String getComments() {
        return comments;
    }

    public void setComments(String comments) {
        this.comments = comments;
    }

    public LocalDateTime getReviewedAt() {
        return reviewedAt;
    }
}
