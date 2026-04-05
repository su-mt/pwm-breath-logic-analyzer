#pragma once
#include <AnalyzerSettings.h>
#include <AnalyzerTypes.h>
#include <memory>

class PWMAnalyzerSettings : public AnalyzerSettings
{
public:
    PWMAnalyzerSettings();
    virtual ~PWMAnalyzerSettings();

    virtual bool SetSettingsFromInterfaces();
    virtual void LoadSettings( const char* settings );
    virtual const char* SaveSettings();

    Channel mInputChannel;

protected:
    std::unique_ptr<AnalyzerSettingInterfaceChannel> mInputChannelInterface;
};
