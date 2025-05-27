import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms'; // Assurez-vous que FormsModule est importé
import { BrowserModule } from '@angular/platform-browser';

import { HttpClientModule } from '@angular/common/http';
import { AppComponent } from './app.component';
import { HomeComponent } from './home/home.component';

@NgModule({
  declarations: [
    AppComponent,
    HomeComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,  // Assurez-vous que FormsModule est ajouté ici
    HttpClientModule // Ajoute ceci pour activer HttpClient

  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
