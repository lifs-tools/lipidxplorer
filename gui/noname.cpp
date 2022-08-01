///////////////////////////////////////////////////////////////////////////
// C++ code generated with wxFormBuilder (version 3.10.1-0-g8feb16b3)
// http://www.wxformbuilder.org/
//
// PLEASE DO *NOT* EDIT THIS FILE!
///////////////////////////////////////////////////////////////////////////

#include "noname.h"

///////////////////////////////////////////////////////////////////////////

MyFrame7::MyFrame7( wxWindow* parent, wxWindowID id, const wxString& title, const wxPoint& pos, const wxSize& size, long style ) : wxFrame( parent, id, title, pos, size, style )
{
	this->SetSizeHints( wxDefaultSize, wxDefaultSize );
	this->SetBackgroundColour( wxSystemSettings::GetColour( wxSYS_COLOUR_MENU ) );

	wxBoxSizer* bSizer11;
	bSizer11 = new wxBoxSizer( wxVERTICAL );

	m_notebook1 = new wxNotebook( this, wxID_ANY, wxDefaultPosition, wxDefaultSize, 0 );
	m_panel5 = new wxPanel( m_notebook1, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxTAB_TRAVERSAL );
	m_panel5->SetToolTip( wxT("Blanks and Quality controls are not used to calculate signal stability") );

	wxBoxSizer* bSizer12;
	bSizer12 = new wxBoxSizer( wxVERTICAL );

	wxBoxSizer* bSizer13;
	bSizer13 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText4 = new wxStaticText( m_panel5, wxID_ANY, wxT("Select Spectra Folder"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText4->Wrap( -1 );
	bSizer13->Add( m_staticText4, 0, wxALL, 5 );

	m_dirPicker1 = new wxDirPickerCtrl( m_panel5, wxID_ANY, wxEmptyString, wxT("Select a folder"), wxDefaultPosition, wxDefaultSize, wxDIRP_DEFAULT_STYLE );
	bSizer13->Add( m_dirPicker1, 1, wxALL, 5 );


	bSizer12->Add( bSizer13, 0, wxEXPAND, 5 );

	m_staticline1 = new wxStaticLine( m_panel5, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxLI_HORIZONTAL );
	bSizer12->Add( m_staticline1, 0, wxEXPAND | wxALL, 5 );

	wxBoxSizer* bSizer131;
	bSizer131 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText41 = new wxStaticText( m_panel5, wxID_ANY, wxT("Select Project or Settings file*"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText41->Wrap( -1 );
	bSizer131->Add( m_staticText41, 0, wxALL, 5 );

	m_filePicker1 = new wxFilePickerCtrl( m_panel5, wxID_ANY, wxEmptyString, wxT("Select a file"), wxT("*.*"), wxDefaultPosition, wxDefaultSize, wxFLP_DEFAULT_STYLE );
	bSizer131->Add( m_filePicker1, 1, wxALL|wxEXPAND, 5 );


	bSizer12->Add( bSizer131, 0, wxEXPAND, 5 );

	m_staticline2 = new wxStaticLine( m_panel5, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxLI_HORIZONTAL );
	bSizer12->Add( m_staticline2, 0, wxEXPAND | wxALL, 5 );

	wxBoxSizer* bSizer18;
	bSizer18 = new wxBoxSizer( wxVERTICAL );

	m_staticText9 = new wxStaticText( m_panel5, wxID_ANY, wxT("Select Spectra by:"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText9->Wrap( -1 );
	m_staticText9->SetFont( wxFont( wxNORMAL_FONT->GetPointSize(), wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false, wxEmptyString ) );

	bSizer18->Add( m_staticText9, 0, wxALL|wxEXPAND, 5 );

	wxBoxSizer* bSizer20;
	bSizer20 = new wxBoxSizer( wxVERTICAL );

	wxBoxSizer* bSizer21;
	bSizer21 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText12 = new wxStaticText( m_panel5, wxID_ANY, wxT("Time range"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText12->Wrap( -1 );
	bSizer21->Add( m_staticText12, 0, wxALL, 5 );

	m_textCtrl9 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer21->Add( m_textCtrl9, 0, wxTOP|wxBOTTOM, 5 );

	m_textCtrl10 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer21->Add( m_textCtrl10, 0, wxTOP|wxBOTTOM, 5 );

	m_staticText13 = new wxStaticText( m_panel5, wxID_ANY, wxT("s"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText13->Wrap( -1 );
	bSizer21->Add( m_staticText13, 0, wxALL, 5 );

	m_staticText22 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText22->Wrap( -1 );
	bSizer21->Add( m_staticText22, 0, wxALL, 5 );

	m_staticText23 = new wxStaticText( m_panel5, wxID_ANY, wxT("LX2"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText23->Wrap( -1 );
	m_staticText23->SetFont( wxFont( wxNORMAL_FONT->GetPointSize(), wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false, wxEmptyString ) );

	bSizer21->Add( m_staticText23, 0, wxALL, 5 );

	m_button6 = new wxButton( m_panel5, wxID_ANY, wxT("Positive mode"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer21->Add( m_button6, 1, wxALL|wxEXPAND, 5 );

	m_button7 = new wxButton( m_panel5, wxID_ANY, wxT("Negavite mode"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer21->Add( m_button7, 1, wxALL|wxEXPAND, 5 );

	m_button8 = new wxButton( m_panel5, wxID_ANY, wxT("Drop Fuzzy"), wxDefaultPosition, wxDefaultSize, 0 );
	m_button8->SetToolTip( wxT("Initial scans oftenhave invalid data, discard these scans?") );

	bSizer21->Add( m_button8, 1, wxALL|wxEXPAND, 5 );


	bSizer20->Add( bSizer21, 1, wxEXPAND, 5 );

	wxBoxSizer* bSizer211;
	bSizer211 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText121 = new wxStaticText( m_panel5, wxID_ANY, wxT("Mass Range"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText121->Wrap( -1 );
	bSizer211->Add( m_staticText121, 0, wxALL, 5 );

	m_textCtrl91 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer211->Add( m_textCtrl91, 0, wxTOP|wxBOTTOM, 5 );

	m_textCtrl101 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer211->Add( m_textCtrl101, 0, wxTOP|wxBOTTOM, 5 );

	m_staticText131 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS1"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText131->Wrap( -1 );
	bSizer211->Add( m_staticText131, 0, wxALL, 5 );

	m_staticText19 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText19->Wrap( -1 );
	bSizer211->Add( m_staticText19, 0, wxALL, 5 );

	m_staticText20 = new wxStaticText( m_panel5, wxID_ANY, wxT("Mass Range"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText20->Wrap( -1 );
	bSizer211->Add( m_staticText20, 0, wxALL, 5 );

	m_textCtrl15 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer211->Add( m_textCtrl15, 0, wxTOP|wxBOTTOM, 5 );

	m_textCtrl16 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer211->Add( m_textCtrl16, 0, wxTOP|wxBOTTOM, 5 );

	m_staticText21 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS2"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText21->Wrap( -1 );
	bSizer211->Add( m_staticText21, 0, wxALL, 5 );


	bSizer20->Add( bSizer211, 1, wxEXPAND, 5 );


	bSizer18->Add( bSizer20, 1, wxEXPAND, 5 );

	wxBoxSizer* bSizer25;
	bSizer25 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText27 = new wxStaticText( m_panel5, wxID_ANY, wxT("LX2"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText27->Wrap( -1 );
	m_staticText27->SetFont( wxFont( wxNORMAL_FONT->GetPointSize(), wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false, wxEmptyString ) );

	bSizer25->Add( m_staticText27, 0, wxALL, 5 );

	m_staticText24 = new wxStaticText( m_panel5, wxID_ANY, wxT("Including Text"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText24->Wrap( -1 );
	bSizer25->Add( m_staticText24, 0, wxALL, 5 );

	m_textCtrl17 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer25->Add( m_textCtrl17, 1, wxTOP|wxBOTTOM|wxRIGHT|wxEXPAND, 5 );

	m_staticText25 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText25->Wrap( -1 );
	bSizer25->Add( m_staticText25, 0, wxALL, 5 );

	m_staticText26 = new wxStaticText( m_panel5, wxID_ANY, wxT("Excluding text"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText26->Wrap( -1 );
	bSizer25->Add( m_staticText26, 0, wxALL|wxEXPAND, 5 );

	m_textCtrl18 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer25->Add( m_textCtrl18, 1, wxALL|wxEXPAND, 5 );


	bSizer18->Add( bSizer25, 0, wxEXPAND, 5 );

	m_staticline3 = new wxStaticLine( m_panel5, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxLI_HORIZONTAL );
	bSizer18->Add( m_staticline3, 0, wxEXPAND | wxALL, 5 );

	wxBoxSizer* bSizer26;
	bSizer26 = new wxBoxSizer( wxVERTICAL );


	bSizer18->Add( bSizer26, 1, wxEXPAND, 5 );


	bSizer12->Add( bSizer18, 0, wxEXPAND, 5 );

	wxBoxSizer* bSizer181;
	bSizer181 = new wxBoxSizer( wxVERTICAL );

	m_staticText91 = new wxStaticText( m_panel5, wxID_ANY, wxT("Select Spectra by:"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText91->Wrap( -1 );
	m_staticText91->SetFont( wxFont( wxNORMAL_FONT->GetPointSize(), wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false, wxEmptyString ) );

	bSizer181->Add( m_staticText91, 0, wxALL|wxEXPAND, 5 );

	wxBoxSizer* bSizer201;
	bSizer201 = new wxBoxSizer( wxVERTICAL );

	wxBoxSizer* bSizer212;
	bSizer212 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText122 = new wxStaticText( m_panel5, wxID_ANY, wxT("Repetition Rate within Spectra"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText122->Wrap( -1 );
	bSizer212->Add( m_staticText122, 0, wxALL|wxEXPAND, 5 );

	m_slider1 = new wxSlider( m_panel5, wxID_ANY, 70, 0, 100, wxDefaultPosition, wxDefaultSize, wxSL_HORIZONTAL );
	bSizer212->Add( m_slider1, 0, wxALL, 5 );

	m_textCtrl43 = new wxTextCtrl( m_panel5, wxID_ANY, wxT("70"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer212->Add( m_textCtrl43, 0, wxALL, 5 );

	m_staticText132 = new wxStaticText( m_panel5, wxID_ANY, wxT("%"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText132->Wrap( -1 );
	bSizer212->Add( m_staticText132, 0, wxALL, 5 );

	m_staticText76 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText76->Wrap( -1 );
	bSizer212->Add( m_staticText76, 0, wxALL, 5 );

	m_button19 = new wxButton( m_panel5, wxID_ANY, wxT("Select Blank"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer212->Add( m_button19, 0, wxALL, 5 );

	m_button191 = new wxButton( m_panel5, wxID_ANY, wxT("QC Spectra"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer212->Add( m_button191, 0, wxALL, 5 );


	bSizer201->Add( bSizer212, 1, wxEXPAND, 5 );

	wxBoxSizer* bSizer2121;
	bSizer2121 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText1221 = new wxStaticText( m_panel5, wxID_ANY, wxT("Found in % of spectra"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText1221->Wrap( -1 );
	bSizer2121->Add( m_staticText1221, 0, wxALL, 5 );

	m_slider11 = new wxSlider( m_panel5, wxID_ANY, 0, 0, 100, wxDefaultPosition, wxDefaultSize, wxSL_HORIZONTAL );
	bSizer2121->Add( m_slider11, 0, wxALL, 5 );

	m_textCtrl431 = new wxTextCtrl( m_panel5, wxID_ANY, wxT("0"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer2121->Add( m_textCtrl431, 0, wxALL, 5 );

	m_staticText1321 = new wxStaticText( m_panel5, wxID_ANY, wxT("%"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText1321->Wrap( -1 );
	bSizer2121->Add( m_staticText1321, 0, wxALL, 5 );

	m_staticText74 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText74->Wrap( -1 );
	m_staticText74->SetToolTip( wxT("|") );

	bSizer2121->Add( m_staticText74, 0, wxALL, 5 );

	m_staticText75 = new wxStaticText( m_panel5, wxID_ANY, wxT("Number of Blanks and QC"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText75->Wrap( -1 );
	bSizer2121->Add( m_staticText75, 0, wxALL, 5 );

	m_textCtrl46 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer2121->Add( m_textCtrl46, 0, wxALL, 5 );


	bSizer201->Add( bSizer2121, 1, wxEXPAND, 5 );

	wxBoxSizer* bSizer2111;
	bSizer2111 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText1211 = new wxStaticText( m_panel5, wxID_ANY, wxT("Signal Intensity"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText1211->Wrap( -1 );
	bSizer2111->Add( m_staticText1211, 0, wxALL, 5 );

	m_textCtrl911 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer2111->Add( m_textCtrl911, 0, wxTOP|wxBOTTOM, 5 );

	wxString m_choice1Choices[] = { wxT("Absolute"), wxT("Relative") };
	int m_choice1NChoices = sizeof( m_choice1Choices ) / sizeof( wxString );
	m_choice1 = new wxChoice( m_panel5, wxID_ANY, wxDefaultPosition, wxDefaultSize, m_choice1NChoices, m_choice1Choices, 0 );
	m_choice1->SetSelection( 0 );
	bSizer2111->Add( m_choice1, 0, wxALL, 5 );

	m_staticText1311 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS1"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText1311->Wrap( -1 );
	bSizer2111->Add( m_staticText1311, 0, wxALL, 5 );

	m_staticText191 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText191->Wrap( -1 );
	bSizer2111->Add( m_staticText191, 0, wxALL, 5 );

	m_staticText12111 = new wxStaticText( m_panel5, wxID_ANY, wxT("Signal Intensity"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText12111->Wrap( -1 );
	bSizer2111->Add( m_staticText12111, 0, wxALL, 5 );

	m_textCtrl151 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer2111->Add( m_textCtrl151, 0, wxTOP|wxBOTTOM, 5 );

	wxString m_choice11Choices[] = { wxT("Absolute"), wxT("Relative") };
	int m_choice11NChoices = sizeof( m_choice11Choices ) / sizeof( wxString );
	m_choice11 = new wxChoice( m_panel5, wxID_ANY, wxDefaultPosition, wxDefaultSize, m_choice11NChoices, m_choice11Choices, 0 );
	m_choice11->SetSelection( 0 );
	bSizer2111->Add( m_choice11, 0, wxALL, 5 );

	m_staticText211 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS2"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText211->Wrap( -1 );
	bSizer2111->Add( m_staticText211, 0, wxALL, 5 );


	bSizer201->Add( bSizer2111, 1, wxEXPAND, 5 );


	bSizer181->Add( bSizer201, 1, wxEXPAND, 5 );


	bSizer12->Add( bSizer181, 0, wxEXPAND, 5 );

	m_staticline7 = new wxStaticLine( m_panel5, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxLI_HORIZONTAL );
	bSizer12->Add( m_staticline7, 0, wxEXPAND | wxALL, 5 );

	wxBoxSizer* bSizer56;
	bSizer56 = new wxBoxSizer( wxVERTICAL );

	m_staticText100 = new wxStaticText( m_panel5, wxID_ANY, wxT("Selection Window and Calibration"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText100->Wrap( -1 );
	m_staticText100->SetFont( wxFont( wxNORMAL_FONT->GetPointSize(), wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false, wxEmptyString ) );

	bSizer56->Add( m_staticText100, 0, wxALL, 5 );

	wxBoxSizer* bSizer57;
	bSizer57 = new wxBoxSizer( wxVERTICAL );

	wxBoxSizer* bSizer58;
	bSizer58 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText102 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS2 precursor grouping tolerance"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText102->Wrap( -1 );
	bSizer58->Add( m_staticText102, 0, wxALL, 5 );

	m_textCtrl60 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer58->Add( m_textCtrl60, 0, wxALL, 5 );

	m_staticText103 = new wxStaticText( m_panel5, wxID_ANY, wxT("Da."), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText103->Wrap( -1 );
	bSizer58->Add( m_staticText103, 0, wxALL, 5 );

	m_button20 = new wxButton( m_panel5, wxID_ANY, wxT("Estimate grouping tolerance"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer58->Add( m_button20, 0, wxALL, 5 );


	bSizer57->Add( bSizer58, 0, wxEXPAND, 5 );

	wxBoxSizer* bSizer59;
	bSizer59 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText104 = new wxStaticText( m_panel5, wxID_ANY, wxT("Calibration masses"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText104->Wrap( -1 );
	bSizer59->Add( m_staticText104, 0, wxALL, 5 );

	m_textCtrl61 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer59->Add( m_textCtrl61, 0, wxALL, 5 );

	m_staticText105 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS1"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText105->Wrap( -1 );
	bSizer59->Add( m_staticText105, 0, wxALL, 5 );

	m_staticText106 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText106->Wrap( -1 );
	bSizer59->Add( m_staticText106, 0, wxALL, 5 );

	m_textCtrl62 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer59->Add( m_textCtrl62, 0, wxALL, 5 );

	m_staticText107 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS2"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText107->Wrap( -1 );
	bSizer59->Add( m_staticText107, 0, wxALL, 5 );

	m_button21 = new wxButton( m_panel5, wxID_ANY, wxT("Suggest Calibration masses"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer59->Add( m_button21, 0, wxALL, 5 );


	bSizer57->Add( bSizer59, 1, wxEXPAND, 5 );


	bSizer56->Add( bSizer57, 1, wxEXPAND, 5 );


	bSizer12->Add( bSizer56, 1, wxEXPAND, 5 );

	m_staticline8 = new wxStaticLine( m_panel5, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxLI_HORIZONTAL );
	bSizer12->Add( m_staticline8, 0, wxEXPAND | wxALL, 5 );

	wxBoxSizer* bSizer60;
	bSizer60 = new wxBoxSizer( wxVERTICAL );

	m_staticText108 = new wxStaticText( m_panel5, wxID_ANY, wxT("Resolution and Tolerance:"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText108->Wrap( -1 );
	m_staticText108->SetFont( wxFont( wxNORMAL_FONT->GetPointSize(), wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false, wxEmptyString ) );

	bSizer60->Add( m_staticText108, 0, wxALL, 5 );

	wxBoxSizer* bSizer61;
	bSizer61 = new wxBoxSizer( wxVERTICAL );

	wxBoxSizer* bSizer62;
	bSizer62 = new wxBoxSizer( wxVERTICAL );

	wxBoxSizer* bSizer591;
	bSizer591 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText1041 = new wxStaticText( m_panel5, wxID_ANY, wxT("Resolution of lowest mass"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText1041->Wrap( -1 );
	bSizer591->Add( m_staticText1041, 0, wxALL, 5 );

	m_textCtrl611 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer591->Add( m_textCtrl611, 0, wxALL, 5 );

	m_staticText1051 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS1"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText1051->Wrap( -1 );
	bSizer591->Add( m_staticText1051, 0, wxALL, 5 );

	m_staticText1061 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText1061->Wrap( -1 );
	bSizer591->Add( m_staticText1061, 0, wxALL, 5 );

	m_textCtrl621 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer591->Add( m_textCtrl621, 0, wxALL, 5 );

	m_staticText1071 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS2 FWHM"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText1071->Wrap( -1 );
	bSizer591->Add( m_staticText1071, 0, wxALL, 5 );

	m_button211 = new wxButton( m_panel5, wxID_ANY, wxT("Suggest Resdolution"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer591->Add( m_button211, 0, wxALL, 5 );

	m_staticText125 = new wxStaticText( m_panel5, wxID_ANY, wxT("FWHM"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText125->Wrap( -1 );
	bSizer591->Add( m_staticText125, 0, wxALL, 5 );


	bSizer62->Add( bSizer591, 1, wxEXPAND, 5 );

	wxBoxSizer* bSizer5911;
	bSizer5911 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText10411 = new wxStaticText( m_panel5, wxID_ANY, wxT("Resolution gradient"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText10411->Wrap( -1 );
	bSizer5911->Add( m_staticText10411, 0, wxALL, 5 );

	m_textCtrl6111 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer5911->Add( m_textCtrl6111, 0, wxALL, 5 );

	m_staticText10511 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS1"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText10511->Wrap( -1 );
	bSizer5911->Add( m_staticText10511, 0, wxALL, 5 );

	m_staticText10611 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText10611->Wrap( -1 );
	bSizer5911->Add( m_staticText10611, 0, wxALL, 5 );

	m_textCtrl6211 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer5911->Add( m_textCtrl6211, 0, wxALL, 5 );

	m_staticText10711 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS2"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText10711->Wrap( -1 );
	bSizer5911->Add( m_staticText10711, 0, wxALL, 5 );

	m_button2111 = new wxButton( m_panel5, wxID_ANY, wxT("Suggest Gradient"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer5911->Add( m_button2111, 0, wxALL, 5 );


	bSizer62->Add( bSizer5911, 1, wxEXPAND, 5 );

	wxBoxSizer* bSizer59111;
	bSizer59111 = new wxBoxSizer( wxHORIZONTAL );

	m_staticText104111 = new wxStaticText( m_panel5, wxID_ANY, wxT("Tolerance"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText104111->Wrap( -1 );
	bSizer59111->Add( m_staticText104111, 0, wxALL, 5 );

	m_textCtrl61111 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer59111->Add( m_textCtrl61111, 0, wxALL, 5 );

	wxString m_choice5Choices[] = { wxT("PPM"), wxT("Da") };
	int m_choice5NChoices = sizeof( m_choice5Choices ) / sizeof( wxString );
	m_choice5 = new wxChoice( m_panel5, wxID_ANY, wxDefaultPosition, wxDefaultSize, m_choice5NChoices, m_choice5Choices, 0 );
	m_choice5->SetSelection( 0 );
	bSizer59111->Add( m_choice5, 0, wxALL, 5 );

	m_staticText105111 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS1"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText105111->Wrap( -1 );
	bSizer59111->Add( m_staticText105111, 0, wxALL, 5 );

	m_staticText106111 = new wxStaticText( m_panel5, wxID_ANY, wxT("|"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText106111->Wrap( -1 );
	bSizer59111->Add( m_staticText106111, 0, wxALL, 5 );

	m_textCtrl62111 = new wxTextCtrl( m_panel5, wxID_ANY, wxEmptyString, wxDefaultPosition, wxDefaultSize, 0 );
	bSizer59111->Add( m_textCtrl62111, 0, wxALL, 5 );

	wxString m_choice51Choices[] = { wxT("PPM"), wxT("Da") };
	int m_choice51NChoices = sizeof( m_choice51Choices ) / sizeof( wxString );
	m_choice51 = new wxChoice( m_panel5, wxID_ANY, wxDefaultPosition, wxDefaultSize, m_choice51NChoices, m_choice51Choices, 0 );
	m_choice51->SetSelection( 0 );
	bSizer59111->Add( m_choice51, 0, wxALL, 5 );

	m_staticText107111 = new wxStaticText( m_panel5, wxID_ANY, wxT("MS2"), wxDefaultPosition, wxDefaultSize, 0 );
	m_staticText107111->Wrap( -1 );
	bSizer59111->Add( m_staticText107111, 0, wxALL, 5 );

	m_button21111 = new wxButton( m_panel5, wxID_ANY, wxT("Suggest Tolerance"), wxDefaultPosition, wxDefaultSize, 0 );
	bSizer59111->Add( m_button21111, 0, wxALL, 5 );


	bSizer62->Add( bSizer59111, 1, wxEXPAND, 5 );


	bSizer61->Add( bSizer62, 1, wxEXPAND, 5 );


	bSizer60->Add( bSizer61, 1, wxEXPAND, 5 );


	bSizer12->Add( bSizer60, 1, wxEXPAND, 5 );


	m_panel5->SetSizer( bSizer12 );
	m_panel5->Layout();
	bSizer12->Fit( m_panel5 );
	m_notebook1->AddPage( m_panel5, wxT("Import Settings"), false );

	bSizer11->Add( m_notebook1, 1, wxEXPAND | wxALL, 5 );


	this->SetSizer( bSizer11 );
	this->Layout();
	m_menubar1 = new wxMenuBar( 0 );
	this->SetMenuBar( m_menubar1 );

	m_statusBar1 = this->CreateStatusBar( 1, wxSTB_SIZEGRIP, wxID_ANY );

	this->Centre( wxBOTH );
}

MyFrame7::~MyFrame7()
{
}
