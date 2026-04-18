// src/redux/interactionSlice.js
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
    hcpName: '',
    interactionType: 'Meeting',
    date: '',
    time: '',
    attendees: '',
    topicsDiscussed: '',
    materialsShared: [],
    samplesDistributed: [],
    sentiment: 'Neutral',
    outcomes: '',
    followUpActions: ''
};

const interactionSlice = createSlice({
    name: 'interaction',
    initialState,
    reducers: {
        updateForm: (state, action) => {
        // This will take the JSON from our AI and update the specific fields
        return { ...state, ...action.payload };
        },
        resetForm: () => initialState
    }
});

export const { updateForm, resetForm } = interactionSlice.actions;
export default interactionSlice.reducer;