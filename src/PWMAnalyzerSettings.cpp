#include "PWMAnalyzerSettings.h"
#include <AnalyzerHelpers.h>

PWMAnalyzerSettings::PWMAnalyzerSettings()
{
    mInputChannelInterface.reset( new AnalyzerSettingInterfaceChannel() );
    mInputChannelInterface->SetTitleAndTooltip( "PWM Channel", "PWM signal input" );
    mInputChannelInterface->SetChannel( mInputChannel );

    AddInterface( mInputChannelInterface.get() );

    AddExportOption( 0, "Export CSV" );
    AddExportExtension( 0, "csv", "csv" );

    ClearChannels();
    AddChannel( mInputChannel, "PWM", false );
}

PWMAnalyzerSettings::~PWMAnalyzerSettings() {}

bool PWMAnalyzerSettings::SetSettingsFromInterfaces()
{
    mInputChannel = mInputChannelInterface->GetChannel();
    ClearChannels();
    AddChannel( mInputChannel, "PWM", true );
    return true;
}

void PWMAnalyzerSettings::LoadSettings( const char* settings )
{
    SimpleArchive archive;
    archive.Init( settings );
    archive >> mInputChannel;

    ClearChannels();
    AddChannel( mInputChannel, "PWM", true );
    UpdateInterfacesFromSettings();
}

const char* PWMAnalyzerSettings::SaveSettings()
{
    SimpleArchive archive;
    archive << mInputChannel;
    return SetReturnString( archive.GetString() );
}
