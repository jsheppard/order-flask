package com.sbsolutions.order.models;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import java.io.Serial;
import java.io.Serializable;
import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;

/**
 * Represents a contact message submitted via the "Contact Us" form.
 * <p>
 * This model captures feedback and inquiries from users, which are then
 * persisted to MongoDB and optionally sent via email to administrators.
 * </p>
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(of = {"id"})
public class ContactMessage implements Serializable {

  @Serial
  private static final long serialVersionUID = 1L;

  /**
   * MongoDB document ID.
   */
  @Id
  private String id;

  /**
   * The name of the person sending the message.
   */
  @NotBlank(message = "Name is required")
  private String name;

  /**
   * The email address of the person sending the message.
   */
  @NotBlank(message = "Email is required")
  @Email(message = "Invalid email format")
  private String email;

  /**
   * The subject of the message.
   */
  @NotBlank(message = "Subject is required")
  private String subject;

  /**
   * The content of the message.
   */
  @NotBlank(message = "Message is required")
  private String message;

  /**
   * The timestamp when the message was submitted.
   */
  @CreatedDate
  private Instant createdAt;
}
