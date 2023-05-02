import React, {useEffect} from 'react';
import GoalDisplay from "./GoalDisplay";

const addr = window.location.origin.split(":3000")[0];

const EndSession = (props) => {
    let endpt = "http://127.0.0.1";

    const handleEndSession = async (event) => {
        event.preventDefault();

        fetch(addr + ':8000/end_session', {
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
            },
            method: "POST",
            body: JSON.stringify({code: props.code, id: props.uuid}),
        });

        // change page
        props.setCode("");
        props.setSessionActive(false);
    };


    return (
        <div>
            <form onSubmit={handleEndSession}>
                <button type="submit">End Session</button>
            </form>
            <br/>
            <GoalDisplay uuid={props.uuid}/>
        </div>
    );
}

export default EndSession;
  