import jsPDF from "jspdf";

/**
 * PDF Generation Utilities for MAPS
 * Handles certificates, reports, and document generation
 */

export interface CertificateOptions {
  userName: string;
  moduleName: string;
  completionDate: Date;
  score?: number;
  instructorName?: string;
  signature?: string;
}

export interface ProgressReportOptions {
  userName: string;
  totalPoints: number;
  level: number;
  modulesCompleted: number;
  changeTalkEvoked: number;
  reflectionsOffered: number;
  completionHistory: Array<{
    moduleName: string;
    completedAt: Date;
    score: number;
  }>;
}

export interface AnalysisReportOptions {
  userName: string;
  transcript: string;
  analysis: {
    miSpiritScore: number;
    techniquesUsed: string[];
    strengths: string[];
    improvements: string[];
    overallFeedback: string;
  };
  date: Date;
}

/**
 * Generate a completion certificate
 */
export function generateCertificate(options: CertificateOptions): jsPDF {
  const pdf = new jsPDF({
    orientation: "landscape",
    unit: "mm",
    format: "a4",
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();

  // Background
  pdf.setFillColor(249, 250, 251);
  pdf.rect(0, 0, pageWidth, pageHeight, "F");

  // Border
  pdf.setDrawColor(20, 184, 166); // MAPS teal
  pdf.setLineWidth(2);
  pdf.rect(10, 10, pageWidth - 20, pageHeight - 20);

  // Inner border
  pdf.setDrawColor(59, 130, 246); // MAPS blue
  pdf.setLineWidth(1);
  pdf.rect(15, 15, pageWidth - 30, pageHeight - 30);

  // Header
  pdf.setFontSize(32);
  pdf.setTextColor(30, 58, 95); // MAPS navy
  pdf.setFont("helvetica", "bold");
  pdf.text("Certificate of Completion", pageWidth / 2, 40, { align: "center" });

  // Subtitle
  pdf.setFontSize(14);
  pdf.setTextColor(107, 114, 128);
  pdf.setFont("helvetica", "normal");
  pdf.text("Motivational Interviewing Training", pageWidth / 2, 50, { align: "center" });

  // Content
  pdf.setFontSize(12);
  pdf.setTextColor(71, 85, 105);
  pdf.text("This is to certify that", pageWidth / 2, 70, { align: "center" });

  // Name
  pdf.setFontSize(28);
  pdf.setTextColor(20, 184, 166);
  pdf.setFont("helvetica", "bold");
  pdf.text(options.userName, pageWidth / 2, 85, { align: "center" });

  // Module
  pdf.setFontSize(12);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");
  pdf.text("has successfully completed", pageWidth / 2, 100, { align: "center" });

  pdf.setFontSize(20);
  pdf.setTextColor(59, 130, 246);
  pdf.setFont("helvetica", "bold");
  pdf.text(options.moduleName, pageWidth / 2, 112, { align: "center" });

  // Date and Score
  pdf.setFontSize(12);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");
  pdf.text(
    `Completed on ${options.completionDate.toLocaleDateString()}`,
    pageWidth / 2,
    130,
    { align: "center" }
  );

  if (options.score !== undefined) {
    pdf.text(
      `with a score of ${options.score}%`,
      pageWidth / 2,
      138,
      { align: "center" }
    );
  }

  // Footer
  pdf.setFontSize(10);
  pdf.setTextColor(156, 163, 175);
  pdf.text(
    "Issued by MAPS - AI Persona System for MI Training",
    pageWidth / 2,
    pageHeight - 20,
    { align: "center" }
  );

  return pdf;
}

/**
 * Generate a progress report
 */
export function generateProgressReport(options: ProgressReportOptions): jsPDF {
  const pdf = new jsPDF();

  const pageWidth = pdf.internal.pageSize.getWidth();
  let yPosition = 20;

  // Header
  pdf.setFillColor(20, 184, 166);
  pdf.rect(0, 0, pageWidth, 40, "F");

  pdf.setFontSize(24);
  pdf.setTextColor(255, 255, 255);
  pdf.setFont("helvetica", "bold");
  pdf.text("Progress Report", pageWidth / 2, 25, { align: "center" });

  yPosition = 55;

  // User Info
  pdf.setFontSize(16);
  pdf.setTextColor(30, 58, 95);
  pdf.setFont("helvetica", "bold");
  pdf.text(options.userName, 20, yPosition);
  yPosition += 10;

  // Stats Cards
  pdf.setFontSize(12);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");

  const stats = [
    { label: "Current Level", value: options.level.toString() },
    { label: "Total Points", value: options.totalPoints.toString() },
    { label: "Modules Completed", value: options.modulesCompleted.toString() },
    { label: "Change Talk Evoked", value: options.changeTalkEvoked.toString() },
    { label: "Reflections Offered", value: options.reflectionsOffered.toString() },
  ];

  for (const stat of stats) {
    pdf.text(`${stat.label}:`, 20, yPosition);
    pdf.text(stat.value, 70, yPosition);
    yPosition += 8;
  }

  yPosition += 10;

  // Completion History
  pdf.setFontSize(14);
  pdf.setTextColor(30, 58, 95);
  pdf.setFont("helvetica", "bold");
  pdf.text("Completion History", 20, yPosition);
  yPosition += 10;

  pdf.setFontSize(10);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");

  for (const completion of options.completionHistory) {
    pdf.text(completion.moduleName, 20, yPosition);
    pdf.text(
      `${completion.completedAt.toLocaleDateString()} - ${completion.score}%`,
      150,
      yPosition
    );
    yPosition += 7;

    // New page if needed
    if (yPosition > 270) {
      pdf.addPage();
      yPosition = 20;
    }
  }

  return pdf;
}

/**
 * Generate an analysis report
 */
export function generateAnalysisReport(options: AnalysisReportOptions): jsPDF {
  const pdf = new jsPDF();

  const pageWidth = pdf.internal.pageSize.getWidth();
  let yPosition = 20;

  // Header
  pdf.setFillColor(59, 130, 246);
  pdf.rect(0, 0, pageWidth, 40, "F");

  pdf.setFontSize(20);
  pdf.setTextColor(255, 255, 255);
  pdf.setFont("helvetica", "bold");
  pdf.text("MAPS Analysis Report", pageWidth / 2, 25, { align: "center" });

  yPosition = 55;

  // User and Date
  pdf.setFontSize(12);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");
  pdf.text(`User: ${options.userName}`, 20, yPosition);
  pdf.text(`Date: ${options.date.toLocaleDateString()}`, 150, yPosition);
  yPosition += 15;

  // MI Spirit Score
  pdf.setFontSize(14);
  pdf.setTextColor(30, 58, 95);
  pdf.setFont("helvetica", "bold");
  pdf.text("MI Spirit Score", 20, yPosition);
  yPosition += 10;

  pdf.setFontSize(12);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");

  // Score bar
  const score = options.analysis.miSpiritScore;
  const barWidth = (score / 100) * 100;

  pdf.setFillColor(200, 200, 200);
  pdf.rect(20, yPosition, 100, 10, "F");
  pdf.setFillColor(20, 184, 166);
  pdf.rect(20, yPosition, barWidth, 10, "F");

  pdf.text(`${score}%`, 130, yPosition + 7);
  yPosition += 20;

  // Techniques Used
  pdf.setFontSize(14);
  pdf.setTextColor(30, 58, 95);
  pdf.setFont("helvetica", "bold");
  pdf.text("Techniques Demonstrated", 20, yPosition);
  yPosition += 10;

  pdf.setFontSize(10);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");

  for (const technique of options.analysis.techniquesUsed) {
    pdf.text(`• ${technique}`, 25, yPosition);
    yPosition += 6;
  }
  yPosition += 10;

  // Strengths
  pdf.setFontSize(14);
  pdf.setTextColor(30, 58, 95);
  pdf.setFont("helvetica", "bold");
  pdf.text("Strengths", 20, yPosition);
  yPosition += 10;

  pdf.setFontSize(10);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");

  for (const strength of options.analysis.strengths) {
    pdf.text(`• ${strength}`, 25, yPosition);
    yPosition += 6;
  }
  yPosition += 10;

  // Areas for Improvement
  pdf.setFontSize(14);
  pdf.setTextColor(30, 58, 95);
  pdf.setFont("helvetica", "bold");
  pdf.text("Areas for Improvement", 20, yPosition);
  yPosition += 10;

  pdf.setFontSize(10);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");

  for (const improvement of options.analysis.improvements) {
    pdf.text(`• ${improvement}`, 25, yPosition);
    yPosition += 6;
  }
  yPosition += 10;

  // Overall Feedback
  pdf.setFontSize(14);
  pdf.setTextColor(30, 58, 95);
  pdf.setFont("helvetica", "bold");
  pdf.text("Overall Feedback", 20, yPosition);
  yPosition += 10;

  pdf.setFontSize(10);
  pdf.setTextColor(71, 85, 105);
  pdf.setFont("helvetica", "normal");

  const lines = pdf.splitTextToSize(options.analysis.overallFeedback, 170);
  pdf.text(lines, 20, yPosition);

  return pdf;
}

/**
 * Convert PDF to Blob for download
 */
export function pdfToBlob(pdf: jsPDF): Blob {
  const pdfOutput = pdf.output("arraybuffer");
  return new Blob([pdfOutput], { type: "application/pdf" });
}

/**
 * Download PDF file
 */
export function downloadPDF(pdf: jsPDF, filename: string): void {
  pdf.save(filename);
}

/**
 * Get PDF data URL for preview
 */
export function getPDFDataUrl(pdf: jsPDF): string {
  return pdf.output("dataurlstring");
}
