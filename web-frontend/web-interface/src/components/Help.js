import React, {useEffect, useState} from 'react';

import HelpText from "./static/HelpText";

const Help = (props) => {
    const [isOpen, setIsOpen] = useState(false);

    const togglePopup = () => {
        setIsOpen(!isOpen);
    }


    return (
        <div style={{position: "absolute", top: 16, right: 16, width: "50%"}}>
            <input
                type="button"
                value={isOpen ? "Close" : "Help"}
                onClick={togglePopup}
                style={{position: "absolute", right: 16}}
            />
            {isOpen && <Popup
                handleClose={togglePopup}
            />}
        </div>
    );
}

export default Help;


const Popup = (props) => {
    return (
        <div style={{
            position: "absolute",
            top: 48,
            right: 16,
            backgroundColor: "#fff",
            boxShadow: "1px 10px 10px #a6a6a6",
            padding: 32,
            borderRadius: 8,
            maxHeight: 400,
            overflowY: "scroll"
        }}>

            <div className="box">
                <b>Help Information</b>
                <HelpText/>
            </div>
        </div>
    );


};