import { CommonModule } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

type View = 'ingreso' | 'salida' | 'historial';
interface Count { ocupados: number; capacidad: number; disponibles: number }
interface Vehicle { placa: string; tipo: 'CARRO' | 'MOTOCICLETA'; titular: string; fecha_vencimiento: string; mensualidad_vigente: boolean; tarifa_mensual_cop: number }
interface Movement { movimiento_id: number; placa: string; tipo: string; operario: string; fecha_hora_entrada: string; fecha_hora_salida: string | null; observacion_entrada: string; observacion_salida: string; estado: 'ABIERTO' | 'CERRADO' }
const API = 'http://127.0.0.1:8000/api/v1';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App implements OnInit {
  private readonly http = inject(HttpClient);
  view: View = 'ingreso';
  occupancy: { CARRO: Count; MOTOCICLETA: Count } | null = null;
  vehicles: Vehicle[] = [];
  movements: Movement[] = [];
  entryPlate = ''; entryNote = ''; exitPlate = ''; exitNote = '';
  historyPlate = ''; fromDate = ''; toDate = ''; historyState = '';
  openMovement: Movement | null = null;
  busy = false; message = ''; messageType: 'success' | 'error' | 'info' = 'info';

  ngOnInit(): void { this.refresh(); }
  setView(view: View): void { this.view = view; this.message = ''; if (view === 'historial') this.loadHistory(); }
  refresh(): void {
    this.http.get<{ CARRO: Count; MOTOCICLETA: Count }>(`${API}/ocupacion`).subscribe({ next: v => this.occupancy = v, error: e => this.showError(e) });
    this.http.get<Vehicle[]>(`${API}/vehiculos`).subscribe({ next: v => this.vehicles = v, error: e => this.showError(e) });
  }
  registerEntry(): void {
    if (this.busy || !this.entryPlate.trim()) return;
    this.busy = true; this.message = '';
    this.http.post<Movement>(`${API}/movimientos/ingresos`, { placa: this.entryPlate, observacion: this.entryNote, operario_id: 1 }).subscribe({
      next: m => { this.busy = false; this.messageType = 'success'; this.message = `Ingreso registrado: ${m.placa} · movimiento #${m.movimiento_id} · ${this.date(m.fecha_hora_entrada)}.`; this.entryPlate = ''; this.entryNote = ''; this.refresh(); },
      error: e => { this.busy = false; this.showError(e); },
    });
  }
  findOpen(): void {
    if (!this.exitPlate.trim()) return;
    this.busy = true; this.openMovement = null; this.message = '';
    this.http.get<Movement>(`${API}/movimientos/abiertos/${encodeURIComponent(this.exitPlate)}`).subscribe({
      next: m => { this.busy = false; this.openMovement = m; this.messageType = 'info'; this.message = `Entrada abierta para ${m.placa}. Confirma la salida para liberar el cupo.`; },
      error: e => { this.busy = false; this.showError(e); },
    });
  }
  registerExit(): void {
    if (!this.openMovement || this.busy) return;
    this.busy = true;
    this.http.post<Movement>(`${API}/movimientos/${this.openMovement.movimiento_id}/salida`, { observacion: this.exitNote, operario_id: 1 }).subscribe({
      next: m => { this.busy = false; this.messageType = 'success'; this.message = `Salida registrada para ${m.placa}. El cupo quedó disponible.`; this.openMovement = null; this.exitPlate = ''; this.exitNote = ''; this.refresh(); },
      error: e => { this.busy = false; this.showError(e); },
    });
  }
  loadHistory(): void {
    const params: Record<string, string> = {};
    if (this.historyPlate.trim()) params['placa'] = this.historyPlate.trim();
    if (this.fromDate) params['desde'] = this.fromDate;
    if (this.toDate) params['hasta'] = this.toDate;
    if (this.historyState) params['estado'] = this.historyState;
    this.http.get<Movement[]>(`${API}/movimientos`, { params }).subscribe({ next: v => this.movements = v, error: e => this.showError(e) });
  }
  showError(error: HttpErrorResponse): void {
    this.messageType = 'error'; const detail = error.error?.detail;
    this.message = typeof detail === 'string' ? detail : detail?.mensaje ?? 'No fue posible conectar con la API. Verifica que el backend esté activo.';
  }
  date(value: string | null): string { return value ? new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : 'En curso'; }
  money(value: number): string { return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value); }
}
