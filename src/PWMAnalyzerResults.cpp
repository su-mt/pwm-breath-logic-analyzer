#include "PWMAnalyzerResults.h"
#include "PWMAnalyzer.h"
#include "PWMAnalyzerSettings.h"
#include <AnalyzerHelpers.h>
#include <cstdio>

PWMAnalyzerResults::PWMAnalyzerResults( PWMAnalyzer* analyzer, PWMAnalyzerSettings* settings )
    : mAnalyzer( analyzer ), mSettings( settings )
{}

PWMAnalyzerResults::~PWMAnalyzerResults() {}

void PWMAnalyzerResults::GenerateBubbleText( U64 frame_index, Channel& channel, DisplayBase display_base )
{
    // FrameV2 is used for data passing to Python HLA.
    // Bubble text is derived from FrameV2 fields stored in mData1/mData2 via old Frame.
    Frame frame = GetFrame( frame_index );

    U64 pulse  = frame.mData1;
    U64 period = frame.mData2;

    double duty = ( period > 0 ) ? ( 100.0 * (double)pulse / (double)period ) : 0.0;

    char text[ 32 ];
    snprintf( text, sizeof( text ), "%.1f%%", duty );
    AddResultString( text );
}

void PWMAnalyzerResults::GenerateExportFile( const char* file, DisplayBase display_base, U32 export_type_user_id )
{
    // MVP: no export
}

void PWMAnalyzerResults::GenerateFrameTabularText( U64 frame_index, DisplayBase display_base )  {}
void PWMAnalyzerResults::GeneratePacketTabularText( U64 packet_id, DisplayBase display_base )    {}
void PWMAnalyzerResults::GenerateTransactionTabularText( U64 transaction_id, DisplayBase display_base ) {}
