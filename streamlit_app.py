import streamlit as st
import pandas as pd

# Initialize session state for acknowledgment
if "acknowledged" not in st.session_state:
    st.session_state["acknowledged"] = False

# Acknowledgment logic
if not st.session_state["acknowledged"]:
    st.warning("⚠️ **IMPORTANT DISCLAIMER**\n\nThis application is for educational and guidance purposes only. All results should be independently verified by qualified healthcare professionals. This tool does not replace clinical judgment or official prescribing information.")
    
    if st.button("I Acknowledge and Understand"):
        st.session_state["acknowledged"] = True
        st.rerun()

if st.session_state["acknowledged"]:
    
    # CTCAE Grading Criteria based on CTCAE v5.0
    ctcae_criteria = {
        'Anemia': {
            'Grade 1': {'Hemoglobin': {'min': 10.0, 'max': 12.6}},  # g/dL
            'Grade 2': {'Hemoglobin': {'min': 8.0, 'max': 9.9}},
            'Grade 3': {'Hemoglobin': {'min': 6.1, 'max': 7.9}},
            'Grade 4': {'Hemoglobin': {'max': 6.0}}
        },
        'Thrombocytopenia': {
            'Grade 1': {'Platelet': {'min': 75, 'max': 150}},  # /mm³
            'Grade 2': {'Platelet': {'min': 50, 'max': 74}},
            'Grade 3': {'Platelet': {'min': 25, 'max': 49}},
            'Grade 4': {'Platelet': {'max': 24}}
        },
        'Leukopenia': {
            'Grade 1': {'WBC': {'min': 3, 'max': 3.9}},  # /mm³
            'Grade 2': {'WBC': {'min': 2, 'max': 2.9}},
            'Grade 3': {'WBC': {'min': 1, 'max': 1.9}},
            'Grade 4': {'WBC': {'max': 0.99}}
        },
        'Neutropenia': {
            'Grade 1': {'ANC': {'min': 1.5, 'max': 1.999}},  # /mm³
            'Grade 2': {'ANC': {'min': 1.0, 'max': 1.499}},
            'Grade 3': {'ANC': {'min': 0.5, 'max': 0.999}},
            'Grade 4': {'ANC': {'max': 0.499}}
        },
        'Acute Kidney Injury': {
            'Grade 1': {'Creatinine_Increase': {'min': 1.5, 'max': 1.9}},  # times baseline
            'Grade 2': {'Creatinine_Increase': {'min': 2.0, 'max': 2.9}},
            'Grade 3': {'Creatinine_Increase': {'min': 3.0, 'max': 5.9}},
            'Grade 4': {'Creatinine_Increase': {'min': 6.0}}
        }
    }

    # Dose modification guidelines
    dose_modifications = {
        'LUTATHERA': {
            'Thrombocytopenia': {
                'Grade 2': 'Withhold dose until resolution to Grade 0-1. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Grade 3': 'Withhold dose until resolution to Grade 0-1. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Grade 4': 'Withhold dose until resolution to Grade 0-1. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Recurrent Grade 2-4': 'Permanently discontinue LUTATHERA.'
            },
            'Anemia': {
                'Grade 3': 'Withhold dose until resolution to Grade 0-2. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Grade 4': 'Withhold dose until resolution to Grade 0-2. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Recurrent Grade 3-4': 'Permanently discontinue LUTATHERA.'
            },
            'Neutropenia': {
                'Grade 3': 'Withhold dose until resolution to Grade 0-2. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Grade 4': 'Withhold dose until resolution to Grade 0-2. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Recurrent Grade 3-4': 'Permanently discontinue LUTATHERA.'
            },
            'Leukopenia': {
                'Grade 2': 'Withhold dose until resolution to Grade 0-1. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Grade 3': 'Withhold dose until resolution to Grade 0-1. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Grade 4': 'Withhold dose until resolution to Grade 0-1. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence.',
                'Recurrent Grade 2-4': 'Permanently discontinue LUTATHERA.'
            },
            'Renal Toxicity': {
                'CLcr < 40 mL/min': 'Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved.',
                '40% increase from baseline creatinine': 'Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved.',
                '40% decrease from baseline CLcr': 'Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved.',
                'Recurrent renal toxicity': 'Permanently discontinue LUTATHERA.'
            },
            'Hepatotoxicity': {
                'Bilirubin > 3x ULN': 'Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved.',
                'Albumin < 30 g/L with INR > 1.5': 'Withhold dose until resolution or return to baseline. Resume at 3.7 GBq if resolved.',
                'Recurrent hepatotoxicity': 'Permanently discontinue LUTATHERA.'
            }
        },
        'PLUVICTO': {
            'Myelosuppression': {
                'Grade 2': 'Withhold PLUVICTO until improvement to Grade 1 or baseline.',
                'Grade ≥ 3': 'Withhold PLUVICTO until improvement to Grade 1 or baseline. Reduce dose by 20% to 5.9 GBq (160 mCi).',
                'Recurrent Grade ≥ 3': 'Permanently discontinue PLUVICTO.'
            },
            'Renal Toxicity': {
                'Grade ≥ 2 creatinine increase': 'Withhold PLUVICTO until improvement.',
                'CLcr < 30 mL/min': 'Withhold PLUVICTO until improvement.',
                '≥40% creatinine increase + >40% CLcr decrease': 'Withhold PLUVICTO until improvement or return to baseline. Reduce dose by 20% to 5.9 GBq.',
                'Grade ≥ 3 renal toxicity': 'Permanently discontinue PLUVICTO.',
                'Recurrent renal toxicity': 'Permanently discontinue PLUVICTO.'
            },
            'Dry Mouth': {
                'Grade 2': 'Withhold PLUVICTO until improvement or return to baseline. Consider reducing dose by 20% to 5.9 GBq.',
                'Grade 3': 'Withhold PLUVICTO until improvement or return to baseline. Reduce dose by 20% to 5.9 GBq.',
                'Recurrent Grade 3': 'Permanently discontinue PLUVICTO.'
            },
            'Fatigue': {
                'Grade ≥ 3': 'Withhold PLUVICTO until improvement to Grade 2 or baseline.'
            },
            'GI Toxicity': {
                'Grade ≥ 3': 'Withhold PLUVICTO until improvement to Grade 2 or baseline. Reduce dose by 20% to 5.9 GBq.',
                'Recurrent Grade ≥ 3': 'Permanently discontinue PLUVICTO.'
            },
            'AST/ALT Elevation': {
                'AST or ALT > 5x ULN without liver metastases': 'Permanently discontinue PLUVICTO.'
            }
        }
    }

    def determine_ctcae_grade(parameter, value, drug=None):
        """Determine CTCAE grade based on parameter value"""
        grades = []
        
        if parameter in ctcae_criteria:
            for grade, limits in ctcae_criteria[parameter].items():
                for lab, thresholds in limits.items():
                    if lab == 'Creatinine_Increase':
                        continue  # Handle separately
                    
                    if value is not None and value > 0:
                        meets_min = 'min' not in thresholds or value >= thresholds['min']
                        meets_max = 'max' not in thresholds or value <= thresholds['max']
                        
                        if meets_min and meets_max:
                            grades.append(grade)
        
        # Return highest grade found
        if grades:
            grade_order = ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4']
            for grade in reversed(grade_order):
                if grade in grades:
                    return grade
        return None

    def assess_renal_function(baseline_creatinine, current_creatinine, baseline_clcr, current_clcr):
        """Assess renal toxicity"""
        issues = []
        
        if current_clcr is not None and current_clcr < 30:
            issues.append("CLcr < 30 mL/min")
        
        if baseline_creatinine and current_creatinine and baseline_creatinine > 0:
            creatinine_increase = current_creatinine / baseline_creatinine
            if creatinine_increase >= 2.0:
                if creatinine_increase >= 3.0:
                    issues.append("Grade ≥ 3 renal toxicity")
                else:
                    issues.append("Grade ≥ 2 creatinine increase")
            
            if creatinine_increase >= 1.4:  # ≥40% increase
                if baseline_clcr and current_clcr and baseline_clcr > 0:
                    clcr_decrease = (baseline_clcr - current_clcr) / baseline_clcr
                    if clcr_decrease > 0.4:  # >40% decrease
                        issues.append("≥40% creatinine increase + >40% CLcr decrease")
        
        return issues

    def assess_hepatotoxicity(bilirubin, albumin, inr, uln_bilirubin=1.0):
        """Assess hepatotoxicity"""
        issues = []
        
        if bilirubin is not None and bilirubin > 3 * uln_bilirubin:
            issues.append("Bilirubin > 3x ULN")
        
        if albumin is not None and inr is not None:
            if albumin < 30 and inr > 1.5:
                issues.append("Albumin < 30 g/L with INR > 1.5")
        
        return issues

    # Streamlit app layout
    st.title("🩺 Radionuclide Therapy Dose Modification Assessment")
    st.markdown("**Based on CTCAE v5.0 and FDA Prescribing Information**")
    
    st.info("📋 This tool evaluates laboratory values against CTCAE criteria and provides dose modification guidance for LUTATHERA and PLUVICTO based on official prescribing information.")

    # Drug selection
    drug = st.selectbox("**Select Radionuclide Therapy**", options=['LUTATHERA', 'PLUVICTO'], key="drug_selection")

    st.markdown("---")
    st.subheader("📊 Laboratory Values")

    # Create columns for better layout
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Hematology**")
        hemoglobin = st.number_input("Hemoglobin (g/dL)", min_value=0.0, value=None, step=0.1, key="hgb")
        platelet = st.number_input("Platelet Count (/mm³)", min_value=0, value=None, step=1000, key="plt")
        wbc = st.number_input("WBC Count (/mm³)", min_value=0, value=None, step=100, key="wbc")
        anc = st.number_input("ANC (/mm³)", min_value=0, value=None, step=100, key="anc")

    with col2:
        st.markdown("**Renal Function**")
        baseline_creatinine = st.number_input("Baseline Creatinine (mg/dL)", min_value=0.0, value=None, step=0.1, key="baseline_cr")
        current_creatinine = st.number_input("Current Creatinine (mg/dL)", min_value=0.0, value=None, step=0.1, key="current_cr")
        baseline_clcr = st.number_input("Baseline Creatinine Clearance (mL/min)", min_value=0.0, value=None, step=1.0, key="baseline_clcr")
        current_clcr = st.number_input("Current Creatinine Clearance (mL/min)", min_value=0.0, value=None, step=1.0, key="current_clcr")

    # Hepatic function
    st.markdown("**Hepatic Function**")
    col3, col4 = st.columns(2)
    with col3:
        bilirubin = st.number_input("Total Bilirubin (mg/dL)", min_value=0.0, value=None, step=0.1, key="bili")
        uln_bilirubin = st.number_input("ULN Bilirubin (mg/dL)", min_value=0.0, value=1.0, step=0.1, key="uln_bili")
    with col4:
        albumin = st.number_input("Albumin (g/L)", min_value=0.0, value=None, step=1.0, key="alb")
        inr = st.number_input("INR", min_value=0.0, value=None, step=0.1, key="inr")

    # Additional fields for PLUVICTO
    if drug == "PLUVICTO":
        st.markdown("**Additional Assessments for PLUVICTO**")
        col5, col6 = st.columns(2)
        
        with col5:
            dry_mouth_grade = st.selectbox(
                "Dry Mouth Grade",
                options=[None, 1, 2, 3],
                format_func=lambda x: (
                    "Select Grade" if x is None
                    else f"Grade {x}: " + {
                        1: "Symptomatic without significant dietary alteration; unstimulated saliva flow >0.2 ml/min",
                        2: "Moderate symptoms; oral intake alterations; unstimulated saliva 0.1 to 0.2 ml/min", 
                        3: "Inability to adequately aliment orally; unstimulated saliva <0.1 ml/min"
                    }.get(x, "")
                ),
                key="dry_mouth"
            )
        
        with col6:
            fatigue_grade = st.selectbox(
                "Fatigue Grade",
                options=[None, 1, 2, 3, 4],
                format_func=lambda x: (
                    "Select Grade" if x is None
                    else f"Grade {x}: " + {
                        1: "Fatigue relieved by rest",
                        2: "Fatigue not relieved by rest; limiting instrumental ADL",
                        3: "Fatigue not relieved by rest; limiting self care ADL",
                        4: "Life-threatening consequences"
                    }.get(x, "")
                ),
                key="fatigue"
            )

        # Liver function for PLUVICTO
        col7, col8 = st.columns(2)
        with col7:
            ast = st.number_input("AST (U/L)", min_value=0.0, value=None, step=1.0, key="ast")
            uln_ast = st.number_input("ULN AST (U/L)", min_value=0.0, value=35.0, step=1.0, key="uln_ast")
        with col8:
            alt = st.number_input("ALT (U/L)", min_value=0.0, value=None, step=1.0, key="alt")
            liver_mets = st.selectbox("Liver Metastases Present?", options=["No", "Yes"], key="liver_mets")

    st.markdown("---")

    # Analysis button
    if st.button("🔍 **Analyze Laboratory Values**", type="primary"):
        
        # Check if any values were entered
        has_values = any([
            hemoglobin, platelet, wbc, anc, current_creatinine, current_clcr,
            bilirubin, albumin, inr
        ])
        
        if drug == "PLUVICTO":
            has_values = has_values or any([dry_mouth_grade, fatigue_grade, ast, alt])
        
        if not has_values:
            st.error("⚠️ Please enter at least one laboratory value to analyze.")
        else:
            # Analyze each parameter
            detected_issues = []
            
            # Hematology assessment
            if hemoglobin is not None:
                grade = determine_ctcae_grade('Anemia', hemoglobin)
                if grade:
                    detected_issues.append(('Anemia', grade, hemoglobin))
            
            if platelet is not None:
                grade = determine_ctcae_grade('Thrombocytopenia', platelet)
                if grade:
                    detected_issues.append(('Thrombocytopenia', grade, platelet))
            
            if wbc is not None:
                grade = determine_ctcae_grade('Leukopenia', wbc)
                if grade:
                    detected_issues.append(('Leukopenia', grade, wbc))
            
            if anc is not None:
                grade = determine_ctcae_grade('Neutropenia', anc)
                if grade:
                    detected_issues.append(('Neutropenia', grade, anc))
            
            # Renal assessment
            renal_issues = assess_renal_function(baseline_creatinine, current_creatinine, baseline_clcr, current_clcr)
            for issue in renal_issues:
                detected_issues.append(('Renal Toxicity', issue, None))
            
            # Hepatic assessment
            hepatic_issues = assess_hepatotoxicity(bilirubin, albumin, inr, uln_bilirubin)
            for issue in hepatic_issues:
                detected_issues.append(('Hepatotoxicity', issue, None))
            
            # PLUVICTO-specific assessments
            if drug == "PLUVICTO":
                if dry_mouth_grade is not None and dry_mouth_grade >= 2:
                    detected_issues.append(('Dry Mouth', f'Grade {dry_mouth_grade}', None))
                
                if fatigue_grade is not None and fatigue_grade >= 3:
                    detected_issues.append(('Fatigue', f'Grade ≥ 3', None))
                
                if ast is not None and liver_mets == "No" and ast > 5 * uln_ast:
                    detected_issues.append(('AST/ALT Elevation', 'AST or ALT > 5x ULN without liver metastases', None))
                
                if alt is not None and liver_mets == "No" and alt > 5 * uln_ast:
                    detected_issues.append(('AST/ALT Elevation', 'AST or ALT > 5x ULN without liver metastases', None))
            
            # Group by myelosuppression for PLUVICTO
            if drug == "PLUVICTO":
                myelo_issues = []
                for issue_type, grade_info, value in detected_issues[:]:
                    if issue_type in ['Anemia', 'Thrombocytopenia', 'Leukopenia', 'Neutropenia']:
                        myelo_issues.append((issue_type, grade_info, value))
                        detected_issues.remove((issue_type, grade_info, value))
                
                if myelo_issues:
                    # Find highest grade
                    highest_grade = 0
                    for _, grade_info, _ in myelo_issues:
                        if 'Grade' in grade_info:
                            grade_num = int(grade_info.split()[1])
                            highest_grade = max(highest_grade, grade_num)
                    
                    if highest_grade >= 2:
                        detected_issues.append(('Myelosuppression', f'Grade {highest_grade}', myelo_issues))

            # Display results
            if detected_issues:
                st.success(f"✅ **Analysis Complete**: Found {len(detected_issues)} issue(s) requiring dose modification review")
                
                st.markdown("---")
                st.subheader("📋 **Dose Modification Recommendations**")
                
                for i, (issue_type, grade_or_condition, details) in enumerate(detected_issues, 1):
                    with st.expander(f"**{i}. {issue_type}: {grade_or_condition}**", expanded=True):
                        
                        # Get dose modification guidance
                        guidance = None
                        drug_modifications = dose_modifications.get(drug, {})
                        
                        if issue_type in drug_modifications:
                            type_modifications = drug_modifications[issue_type]
                            
                            # Try exact match first
                            if grade_or_condition in type_modifications:
                                guidance = type_modifications[grade_or_condition]
                            else:
                                # Try partial matches
                                for key, value in type_modifications.items():
                                    if grade_or_condition in key or any(term in grade_or_condition for term in key.split()):
                                        guidance = value
                                        break
                        
                        if guidance:
                            st.markdown(f"**📝 Recommendation:** {guidance}")
                        else:
                            st.warning("⚠️ No specific dose modification guidance found. Consult prescribing information.")
                        
                        # Show supporting data
                        if details and isinstance(details, list):
                            st.markdown("**Supporting Laboratory Values:**")
                            for detail_type, detail_grade, detail_value in details:
                                if detail_value is not None:
                                    st.markdown(f"• {detail_type}: {detail_value} ({detail_grade})")
                                else:
                                    st.markdown(f"• {detail_type}: {detail_grade}")
                        elif details is not None:
                            st.markdown(f"**Value:** {details}")
                
                # Additional notes
                st.markdown("---")
                st.info("ℹ️ **Important Notes:**\n"
                       "• These recommendations are based on FDA prescribing information\n" 
                       "• Consider patient's overall clinical condition\n"
                       "• Monitor closely and reassess before each dose\n"
                       "• Consult full prescribing information for complete guidance")
                
            else:
                st.success("✅ **No adverse events requiring dose modification detected** based on the entered laboratory values.")
                st.info("Continue monitoring per standard protocols and reassess before next dose.")

    # Footer
    st.markdown("---")
    st.markdown("*Based on CTCAE v5.0 and current FDA prescribing information for LUTATHERA and PLUVICTO*")
    st.caption("⚠️ This tool is for educational purposes only and does not replace clinical judgment.")