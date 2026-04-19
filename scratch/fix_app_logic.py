        with analyzer_tabs[3]:
            st.markdown("""
            <div style='background-color: #1a1a1a; padding: 25px; border-radius: 15px; border: 1px solid #333; margin-bottom: 25px;'>
                <h2 style='color: #4CAF50; margin-bottom: 10px;'>🎙️ AI Voice-to-Voice Mock Interview</h2>
                <p style='color: #888;'>Practice your interview skills with our formal AI interviewer. Scraped real-world questions will be used to test you.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Initialize Utilities
            audio_utils = AudioUtils()
            interview_manager = InterviewManager()
            
            # 1. Interview is Active
            if 'interview' in st.session_state and not st.session_state.interview.get('is_complete', False):
                session = st.session_state.interview
                
                # Header Section
                st.markdown(f"### {session['role']} Interview at {session['company']}")
                progress = 0
                if session['current_step'].startswith('question_'):
                    progress = (session['question_index'] + 1) / (session['target_length'] + 2) # +2 for Greeting & Intro
                
                st.progress(progress)
                
                # Main Interaction Loop
                chat_container = st.container(height=400)
                
                with chat_container:
                    for item in session['transcript']:
                        with st.chat_message(item['role'].lower()):
                            st.write(item['text'])
                            if item['role'] == "User" and 'score' in item:
                                # Show inline feedback
                                st.markdown(f"⭐ **Score:** {item['score']}/10")
                                st.caption(f"Analysis: {item['feedback']}")
                
                # Logic for current step
                if 'last_handled_step' not in st.session_state or st.session_state.last_handled_step != session['current_step']:
                    # AI needs to speak
                    message = ""
                    if session['current_step'] == "greeting":
                        message = f"Hello! I am your interviewer today for the '{session['role']}' position at '{session['company']}'. I'll be asking you {session['target_length']} questions. To start, could you please tell me a bit about yourself?"
                    elif session['current_step'] == "intro":
                        message = "Thank you. Let's get started with the first question."
                        session['current_step'] = "question_0"
                        st.rerun()
                    elif session['current_step'].startswith('question_'):
                        idx = session['question_index']
                        if idx < len(session['questions']):
                            message = session['questions'][idx]['question']
                        else:
                            # If we ran out of scraped questions, AI generates one
                            prompt = f"Ask a formal interview question for {session['role']} at {session['company']}."
                            from utils.llm_orchestrator import LLMOrchestrator
                            message, _ = LLMOrchestrator().generate_content(prompt)
                    elif session['current_step'] == "conclusion":
                        message = "That concludes our interview. Thank you for your time. Your report is now ready for download."
                        session['is_complete'] = True
                    
                    if message:
                        session['transcript'].append({"role": "AI", "text": message, 
                                                     "question_idx": session['question_index'] if session['current_step'].startswith('question_') else None})
                        st.session_state.last_handled_step = session['current_step']
                        audio = audio_utils.text_to_speech(message, mode=session['language_mode'])
                        audio_utils.autoplay_audio(audio)
                        
                        # Handle Continuous Mode JS Bridge
                        if session.get('continuous_mode'):
                            # Inject JS to auto-click the mic recorder after audio finishes
                            st.components.v1.html("""
                                <script>
                                    window.parent.addEventListener('message', function(event) {
                                        if (event.data.type === 'audio_finished') {
                                            console.log("Audio finished event received in app.py bridge");
                                            // Find the mic recorder button and click it
                                            const buttons = window.parent.document.querySelectorAll('button');
                                            for(const btn of buttons) {
                                                if(btn.innerText.includes("Click to Start Recording")) {
                                                    btn.click();
                                                    console.log("Auto-started recorder");
                                                    break;
                                                }
                                            }
                                        }
                                    });
                                </script>
                            """, height=0, width=0)
                            
                        st.rerun()
                
                # User Input Section
                if not session['is_complete']:
                    st.markdown("---")
                    st.write("🎙️ **Record your answer below:**")
                    audio_input = mic_recorder(
                        start_prompt="Click to Start Recording",
                        stop_prompt="Click to Stop & Send",
                        key='recorder',
                        use_container_width=True
                    )
                    
                    if audio_input:
                        with st.spinner("Processing..."):
                            transcript = audio_utils.transcribe_audio(audio_input['bytes'])
                            session['transcript'].append({"role": "User", "text": transcript})
                            
                            # Process based on step
                            if session['current_step'] == "greeting":
                                session['current_step'] = "intro"
                            elif session['current_step'].startswith('question_'):
                                # Evaluate Answer
                                q_text = session['transcript'][-2]['text']
                                evaluation = interview_manager.evaluate_answer(q_text, transcript)
                                # Append evaluation to transcript for report
                                session['transcript'][-1].update(evaluation)
                                
                                session['question_index'] += 1
                                if session['question_index'] >= session['target_length']:
                                    session['current_step'] = "conclusion"
                                else:
                                    session['current_step'] = f"question_{session['question_index']}"
                            
                            st.rerun()
            
            # 3. Post Interview - Results Dashboard
            elif 'interview' in st.session_state and st.session_state.interview.get('is_complete', False):
                session = st.session_state.interview
                st.success("🎉 Interview Completed!")
                
                # Store report in session state to avoid regeneration issues
                if 'final_report_pdf' not in st.session_state:
                    with st.spinner("Analyzing your performance and generating report..."):
                        st.session_state.final_report_pdf = interview_manager.generate_pdf_report()
                
                # Show summary stats
                total_q = session['target_length']
                total_score = sum(item.get('score', 0) for item in session['transcript'] if item['role'] == "User")
                avg_score = total_score / total_q if total_q > 0 else 0
                
                col_r1, col_r2, col_r3 = st.columns(3)
                col_r1.metric("Average Score", f"{avg_score:.1f}/10")
                col_r2.metric("Questions Faced", total_q)
                col_r3.metric("Status", "Completed")
                
                st.download_button(
                    label="📄 Download Detailed Performance Report (PDF)",
                    data=st.session_state.final_report_pdf,
                    file_name=f"interview_report_{session['company']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
                
                # Show full transcript with detailed feedback
                with st.expander("👁️ View Full Transcript & Detailed Feedback", expanded=True):
                    for item in session['transcript']:
                        with st.chat_message(item['role'].lower()):
                            st.write(item['text'])
                            if item['role'] == "User" and 'score' in item:
                                st.markdown(f"**Score:** {item['score']}/10")
                                st.markdown(f"**Analysis:** {item['feedback']}")
                                st.info(f"💡 **Tip:** {item.get('improvement', 'N/A')}")
                
                if st.button("🔄 Start New Interview", use_container_width=True):
                    if 'final_report_pdf' in st.session_state:
                        del st.session_state.final_report_pdf
                    del st.session_state.interview
                    if 'last_handled_step' in st.session_state:
                        del st.session_state.last_handled_step
                    st.rerun()

            # 2. Setup Panel - Only show if no interview
            else:
                # Setup Panel
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    mock_role = st.text_input("Target Role", placeholder="e.g. Software Engineer", key="mock_role_input")
                with col_s2:
                    mock_company = st.text_input("Target Company", placeholder="e.g. Google", key="mock_company_input")
                col_s3, col_s4 = st.columns([2, 1])
                with col_s3:
                    mock_length = st.slider("Number of Questions", 3, 8, 5)
                with col_s4:
                    continuous_mode = st.toggle("🔄 Continuous Listening", value=True, help="Automatically starts microphone after AI speaks")
                
                mock_lang = st.radio("Language Mode", ["English", "Hinglish"], horizontal=True)
                
                if st.button("🚀 Start Voice Interview", type="primary", use_container_width=True):
                    if mock_role and mock_company:
                        # Try to get scraped questions or use fallback
                        from utils.interview_fetcher import InterviewFetcher
                        fetcher = InterviewFetcher()
                        with st.spinner("Preparing your interview board..."):
                            questions, _, context = fetcher.fetch_all(mock_company, mock_role)
                            interview_manager.initialize_session(questions or [], mock_role, mock_company, mock_length, mock_lang)
                            st.session_state.interview['continuous_mode'] = continuous_mode
                            st.rerun()
                    else:
                        st.warning("Please provide both role and company.")
