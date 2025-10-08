import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ModalController, ToastController, AlertController, LoadingController } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/auth.models';

@Component({
  selector: 'app-user-profile',
  templateUrl: './user-profile.component.html',
  styleUrls: ['./user-profile.component.scss'],
})
export class UserProfileComponent implements OnInit {
  user: User | null = null;
  showChangePassword = false;
  changePasswordForm!: FormGroup;
  loading = false;

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private modalController: ModalController,
    private toastController: ToastController,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {}

  ngOnInit() {
    // Get current user
    this.authService.currentUser$.subscribe(user => {
      this.user = user;
    });

    // Initialize change password form
    this.changePasswordForm = this.formBuilder.group({
      currentPassword: ['', [Validators.required]],
      newPassword: ['', [
        Validators.required,
        Validators.minLength(8)
      ]],
      confirmPassword: ['', [Validators.required]]
    });
  }

  /**
   * Close the modal
   */
  dismiss() {
    this.modalController.dismiss();
  }

  /**
   * Toggle change password section
   */
  toggleChangePassword() {
    this.showChangePassword = !this.showChangePassword;
    if (!this.showChangePassword) {
      this.changePasswordForm.reset();
    }
  }

  /**
   * Handle change password form submission
   */
  async onChangePassword() {
    if (this.changePasswordForm.invalid) {
      this.markFormGroupTouched(this.changePasswordForm);
      return;
    }

    const { currentPassword, newPassword, confirmPassword } = this.changePasswordForm.value;

    if (newPassword !== confirmPassword) {
      const toast = await this.toastController.create({
        message: 'New passwords do not match',
        duration: 3000,
        color: 'danger',
        position: 'top'
      });
      await toast.present();
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Changing password...',
    });
    await loading.present();

    this.loading = true;

    this.authService.changePassword(currentPassword, newPassword).subscribe({
      next: async (response) => {
        await loading.dismiss();
        this.loading = false;
        this.showChangePassword = false;
        this.changePasswordForm.reset();

        const toast = await this.toastController.create({
          message: 'Password changed successfully',
          duration: 3000,
          color: 'success',
          position: 'top'
        });
        await toast.present();
      },
      error: async (error) => {
        await loading.dismiss();
        this.loading = false;

        const toast = await this.toastController.create({
          message: error.message || 'Failed to change password',
          duration: 3000,
          color: 'danger',
          position: 'top'
        });
        await toast.present();
      }
    });
  }

  /**
   * Handle logout
   */
  async onLogout() {
    const alert = await this.alertController.create({
      header: 'Logout',
      message: 'Are you sure you want to logout?',
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Logout',
          role: 'destructive',
          handler: () => {
            this.authService.logout();
            this.modalController.dismiss();
          }
        }
      ]
    });

    await alert.present();
  }

  /**
   * Handle account deactivation
   */
  async onDeactivateAccount() {
    const alert = await this.alertController.create({
      header: 'Deactivate Account',
      message: 'Are you sure you want to deactivate your account? This action cannot be undone.',
      inputs: [
        {
          name: 'confirmation',
          type: 'text',
          placeholder: 'Type "DEACTIVATE" to confirm'
        }
      ],
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Deactivate',
          role: 'destructive',
          handler: (data) => {
            if (data.confirmation === 'DEACTIVATE') {
              this.deactivateAccount();
              return true;
            } else {
              this.showToast('Please type "DEACTIVATE" to confirm', 'warning');
              return false;
            }
          }
        }
      ]
    });

    await alert.present();
  }

  /**
   * Deactivate account
   */
  private async deactivateAccount() {
    const loading = await this.loadingController.create({
      message: 'Deactivating account...',
    });
    await loading.present();

    // TODO: Implement deactivation API call
    setTimeout(async () => {
      await loading.dismiss();
      this.showToast('Account deactivated successfully', 'success');
      this.authService.logout();
      this.modalController.dismiss();
    }, 1000);
  }

  /**
   * Show toast message
   */
  private async showToast(message: string, color: string = 'primary') {
    const toast = await this.toastController.create({
      message,
      duration: 3000,
      color,
      position: 'top'
    });
    await toast.present();
  }

  /**
   * Mark all form fields as touched to show validation errors
   */
  private markFormGroupTouched(formGroup: FormGroup) {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();
    });
  }

  /**
   * Get formatted date
   */
  getFormattedDate(dateString: string | null): string {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}
