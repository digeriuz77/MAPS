import { NextRequest, NextResponse } from "next/server";
import { generateCertificate, pdfToBlob } from "@/lib/pdf/generator";

/**
 * Generate PDF document
 * POST /api/pdf/generate
 *
 * Body: {
 *   type: "certificate" | "progress-report" | "analysis-report"
 *   data: object (type-specific data)
 * }
 */
export async function POST(req: NextRequest) {
  try {
    const { type, data } = await req.json();

    if (!type || !data) {
      return NextResponse.json(
        { error: "Type and data are required" },
        { status: 400 }
      );
    }

    let pdf;

    switch (type) {
      case "certificate":
        pdf = generateCertificate({
          userName: data.userName || "User",
          moduleName: data.moduleName || "Module",
          completionDate: new Date(data.completionDate || Date.now()),
          score: data.score,
          instructorName: data.instructorName,
        });
        break;

      case "progress-report":
        pdf = generateProgressReport({
          userName: data.userName || "User",
          totalPoints: data.totalPoints || 0,
          level: data.level || 1,
          modulesCompleted: data.modulesCompleted || 0,
          changeTalkEvoked: data.changeTalkEvoked || 0,
          reflectionsOffered: data.reflectionsOffered || 0,
          completionHistory: data.completionHistory || [],
        });
        break;

      case "analysis-report":
        pdf = generateAnalysisReport({
          userName: data.userName || "User",
          transcript: data.transcript || "",
          analysis: data.analysis || {
            miSpiritScore: 0,
            techniquesUsed: [],
            strengths: [],
            improvements: [],
            overallFeedback: "",
          },
          date: new Date(data.date || Date.now()),
        });
        break;

      default:
        return NextResponse.json(
          { error: "Invalid PDF type" },
          { status: 400 }
        );
    }

    // Convert to blob
    const blob = pdfToBlob(pdf);

    // Return as response
    return new NextResponse(blob, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${type}-${Date.now()}.pdf"`,
      },
    });
  } catch (error) {
    console.error("PDF generation error:", error);
    return NextResponse.json(
      {
        error: "PDF generation failed",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
