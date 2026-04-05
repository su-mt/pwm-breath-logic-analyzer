#include "PWMAnalyzer.h"
#include "PWMAnalyzerResults.h"
#include <AnalyzerChannelData.h>

PWMAnalyzer::PWMAnalyzer() : mPWM( nullptr )
{
    SetAnalyzerSettings( &mSettings );
    UseFrameV2();   // enables named fields readable by Python HLA
}

PWMAnalyzer::~PWMAnalyzer()
{
    KillThread();
}

void PWMAnalyzer::SetupResults()
{
    mResults.reset( new PWMAnalyzerResults( this, &mSettings ) );
    SetAnalyzerResults( mResults.get() );
    mResults->AddChannelBubblesWillAppearOn( mSettings.mInputChannel );
}

void PWMAnalyzer::WorkerThread()
{
    mPWM = GetAnalyzerChannelData( mSettings.mInputChannel );

    // Align to a rising edge so every iteration starts consistently
    if( mPWM->GetBitState() == BIT_LOW )
        mPWM->AdvanceToNextEdge();

    while( true )
    {
        // ── Rising edge: start of pulse ──────────────────────────────
        U64 t_rise = mPWM->GetSampleNumber();

        // ── Falling edge: end of pulse ───────────────────────────────
        mPWM->AdvanceToNextEdge();
        U64 t_fall = mPWM->GetSampleNumber();

        // ── Next rising edge: start of next period ───────────────────
        mPWM->AdvanceToNextEdge();
        U64 t_next_rise = mPWM->GetSampleNumber();

        U64 pulse_width = t_fall - t_rise;
        U64 period      = t_next_rise - t_rise;

        // ── FrameV2: named fields consumed by Python HLA ─────────────
        FrameV2 fv2;
        fv2.AddInteger( "pulse_width", pulse_width );
        fv2.AddInteger( "period",      period );
        mResults->AddFrameV2( fv2, "pwm", t_rise, t_next_rise - 1 );

        // ── Old Frame: bubble text on the C++ analyzer track ─────────
        Frame frame;
        frame.mStartingSampleInclusive = t_rise;
        frame.mEndingSampleInclusive   = t_next_rise - 1;
        frame.mData1  = pulse_width;
        frame.mData2  = period;
        frame.mType   = 0;
        frame.mFlags  = 0;
        mResults->AddFrame( frame );

        mResults->CommitResults();
        ReportProgress( t_next_rise );
        CheckIfThreadShouldExit();
    }
}

// ── No simulation needed for MVP ─────────────────────────────────────────────
U32 PWMAnalyzer::GenerateSimulationData( U64, U32, SimulationChannelDescriptor** )
{
    return 0;
}

U32  PWMAnalyzer::GetMinimumSampleRateHz() { return 10'000; }
bool PWMAnalyzer::NeedsRerun()             { return false;  }
const char* PWMAnalyzer::GetAnalyzerName() const { return "PWM Decoder"; }

// ── Required C exports ────────────────────────────────────────────────────────
extern "C" ANALYZER_EXPORT const char* __cdecl GetAnalyzerName()
{
    return "PWM Decoder";
}
extern "C" ANALYZER_EXPORT Analyzer* __cdecl CreateAnalyzer()
{
    return new PWMAnalyzer();
}
extern "C" ANALYZER_EXPORT void __cdecl DestroyAnalyzer( Analyzer* analyzer )
{
    delete analyzer;
}
