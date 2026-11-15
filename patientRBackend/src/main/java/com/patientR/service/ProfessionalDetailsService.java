
package com.patientR.service;

import com.patientR.entity.Professional;
import com.patientR.repo.ProfessionalRepository;

import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class ProfessionalDetailsService implements UserDetailsService {

    private final ProfessionalRepository professionalRepository;

    public ProfessionalDetailsService(
            ProfessionalRepository professionalRepository) {
        this.professionalRepository = professionalRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String email)
            throws UsernameNotFoundException {

        Professional professional = professionalRepository
                .findByEmail(email)
                .orElseThrow(() ->
                        new UsernameNotFoundException(
                                "Professional not found"));

        System.out.println("Professional found: " + professional.getEmail());
        System.out.println("Professional active: " + professional.isActive());
        System.out.println("Professional role: " + professional.getRole());

        return User.withUsername(professional.getEmail())
                .password(professional.getPassword())
                .roles(professional.getRole())
                .disabled(!professional.isActive())
                .build();
    }
}
