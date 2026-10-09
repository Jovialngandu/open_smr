import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { SettingsService } from './features/settings/services/settings.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
})
export class App {
  constructor() {
    inject(SettingsService);
  }
}
