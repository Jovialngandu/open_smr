import { Component, inject, signal } from '@angular/core';
import { LucideShieldCheck, LucideCircleAlert, LucideArrowRight } from '@lucide/angular';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule, RouterLink, LucideShieldCheck, LucideCircleAlert, LucideArrowRight],
  host: { class: 'auth-page' },
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly formBuilder = inject(FormBuilder);
  protected readonly passwordVisible = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly form = this.formBuilder.nonNullable.group(
    {
      firstName: [''],
      lastName: [''],
      email: ['', [Validators.required, Validators.email]],
      username: ['', [Validators.required, Validators.minLength(3)]],
      organizationMode: ['LATER' as 'CREATE' | 'JOIN' | 'LATER'],
      organization: [''],
      organizationCode: [''],
      password: ['', [Validators.required, Validators.minLength(12), Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/)]],
      confirmation: ['', Validators.required],
      terms: [false, Validators.requiredTrue],
    },
    { validators: passwordMatchValidator },
  );
  protected passwordStrength(): number {
    const value = this.form.controls.password.value;
    return [value.length >= 12, /[a-z]/.test(value) && /[A-Z]/.test(value), /\d/.test(value), /[^\w]/.test(value)].filter(Boolean).length;
  }

  protected invalid(controlName: keyof typeof this.form.controls): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.touched || control.dirty);
  }

  protected submit(): void {
    this.errorMessage.set('');
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    if (value.organizationMode === 'CREATE' && !value.organization.trim()) {
      this.form.controls.organization.setErrors({ required: true });
      this.form.controls.organization.markAsTouched();
      return;
    }
    if (value.organizationMode === 'JOIN' && !value.organizationCode.trim()) {
      this.form.controls.organizationCode.setErrors({ required: true });
      this.form.controls.organizationCode.markAsTouched();
      return;
    }
    this.auth.register({
      first_name: value.firstName.trim(),
      last_name: value.lastName.trim(),
      email: value.email.trim().toLowerCase(),
      username: value.username.trim(),
      password: value.password,
      organization_name: value.organizationMode === 'CREATE' ? value.organization.trim() : undefined,
      join_organization_code: value.organizationMode === 'JOIN' ? value.organizationCode.trim().toUpperCase() : undefined,
    }).subscribe({
      next: () => void this.router.navigate(['/select-context']),
      error: (error: Error) => this.errorMessage.set(error.message),
    });
  }
}

function passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
  return control.get('password')?.value === control.get('confirmation')?.value
    ? null
    : { passwordMismatch: true };
}
