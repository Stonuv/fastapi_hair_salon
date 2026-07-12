/** Зеркало ALLOWED_TRANSITIONS из backend/app/services/appointment_service.py — только для UI (кнопки),
 * окончательную проверку всегда делает сервер. */
export const ALLOWED_TRANSITIONS = {
  pending: ['confirmed', 'cancelled'],
  confirmed: ['done', 'cancelled'],
  done: [],
  cancelled: [],
}

export const STATUS_ACTION_LABELS = {
  confirmed: 'Подтвердить',
  done: 'Завершить',
  cancelled: 'Отменить',
}

/** Зеркало проверки в AppointmentService.reschedule() — перенос доступен
 * только для незавершённых записей. */
export const RESCHEDULABLE_STATUSES = ['pending', 'confirmed']
