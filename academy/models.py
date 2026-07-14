from datetime import date

from django.conf import settings
from django.db import models


class CategoriaCorso(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Categoria corso"
        verbose_name_plural = "Categorie corso"

    def __str__(self):
        return self.nome


class CorsoAcademy(models.Model):
    titolo = models.CharField(max_length=200)
    descrizione = models.TextField(blank=True, default="")
    categoria = models.ForeignKey(
        CategoriaCorso,
        on_delete=models.PROTECT,
        related_name="corsi",
    )
    durata_ore = models.PositiveIntegerField()
    obbligatorio = models.BooleanField(default=False)
    attivo = models.BooleanField(default=True)
    data_creazione = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["titolo"]
        verbose_name = "Corso Academy"
        verbose_name_plural = "Corsi Academy"

    def __str__(self):
        return self.titolo


class AssegnazioneCorso(models.Model):
    class Stato(models.TextChoices):
        ASSEGNATO = "ASSEGNATO", "Assegnato"
        COMPLETATO = "COMPLETATO", "Completato"
        SCADUTO = "SCADUTO", "Scaduto"
        ANNULLATO = "ANNULLATO", "Annullato"

    corso = models.ForeignKey(
        CorsoAcademy,
        on_delete=models.PROTECT,
        related_name="assegnazioni",
    )
    dipendente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assegnazioni",
    )
    data_assegnazione = models.DateField(default=date.today)
    data_scadenza = models.DateField()
    stato = models.CharField(
        max_length=20,
        choices=Stato.choices,
        default=Stato.ASSEGNATO,
    )
    data_completamento = models.DateField(null=True, blank=True)
    data_creazione = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_assegnazione", "-id"]
        verbose_name = "Assegnazione corso"
        verbose_name_plural = "Assegnazioni corso"

    def __str__(self):
        return f"#{self.pk} - {self.corso} -> {self.dipendente} ({self.stato_effettivo})"

    @property
    def is_scaduto(self):
        if self.stato != self.Stato.ASSEGNATO:
            return False
        if self.data_scadenza is None:
            return False
        return self.data_scadenza < date.today()

    @property
    def stato_effettivo(self):
        if self.is_scaduto:
            return self.Stato.SCADUTO
        return self.stato

    @property
    def stato_effettivo_display(self):
        return self.Stato(self.stato_effettivo).label
