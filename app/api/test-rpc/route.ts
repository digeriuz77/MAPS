import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * Test endpoint to verify RPC function works
 * GET /api/test-rpc
 */
export async function GET() {
    try {
        const supabase = await createClient();

        // Test the RPC function
        const { data, error } = await supabase.rpc("get_debug_info");

        if (error) {
            return NextResponse.json({
                success: false,
                error: error.message,
                details: error,
                hint: "Make sure you ran the migration in Supabase SQL Editor"
            }, { status: 500 });
        }

        return NextResponse.json({
            success: true,
            message: "RPC function is working!",
            data
        });
    } catch (error) {
        return NextResponse.json({
            success: false,
            error: error instanceof Error ? error.message : String(error),
        }, { status: 500 });
    }
}
