#pragma once
#include <Analyzer.h>
#include "PWMAnalyzerSettings.h"
#include "PWMAnalyzerResults.h"
#include <memory>

class PWMAnalyzer : public Analyzer2
{
public:
    PWMAnalyzer();
    virtual ~PWMAnalyzer();

    virtual void SetupResults();
    virtual void WorkerThread();

    virtual U32  GenerateSimulationData( U64 newest_sample, U32 sample_rate,
                                         SimulationChannelDescriptor** simulation_channels );
    virtual U32  GetMinimumSampleRateHz();
    virtual const char* GetAnalyzerName() const;
    virtual bool NeedsRerun();

protected:
    PWMAnalyzerSettings              mSettings;
    std::unique_ptr<PWMAnalyzerResults> mResults;
    AnalyzerChannelData*             mPWM;
};
