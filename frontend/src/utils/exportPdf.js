// src/utils/exportPdf.js
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

/**
 * Exporta el DOM de un contenedor (ref) a un PDF apaisado con cabecera
 * institucional UTP. Usado tanto por el horario administrativo como
 * por el horario personal del estudiante.
 */
export async function exportarHorarioPDF(elemento, { titulo, subtitulo, nombreArchivo }) {
  if (!elemento) return;

  const canvas = await html2canvas(elemento, { scale: 2, backgroundColor: '#ffffff' });
  const imgData = canvas.toDataURL('image/png');

  const pdf = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
  const pageW = pdf.internal.pageSize.getWidth();
  const pageH = pdf.internal.pageSize.getHeight();

  // ── Cabecera institucional ──
  pdf.setFillColor('#8B0000');
  pdf.rect(0, 0, pageW, 46, 'F');
  pdf.setTextColor('#FFFFFF');
  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(14);
  pdf.text(titulo || 'Demanda Aulas Matrícula IA', 24, 22);
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(9);
  pdf.text(subtitulo || 'UTP · Campus Lima Sur', 24, 36);

  // ── Imagen de la grilla, escalada al ancho de página ──
  const marginX = 24;
  const marginTop = 60;
  const maxW = pageW - marginX * 2;
  const maxH = pageH - marginTop - 24;
  const ratio = Math.min(maxW / canvas.width, maxH / canvas.height);
  const w = canvas.width * ratio;
  const h = canvas.height * ratio;

  pdf.addImage(imgData, 'PNG', marginX, marginTop, w, h);
  pdf.save(nombreArchivo || 'horario.pdf');
}
