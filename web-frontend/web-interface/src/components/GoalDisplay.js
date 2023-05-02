import React, {useEffect, useState} from 'react';
import Axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Collapsible from 'react-collapsible';

const addr = window.location.origin.split(":3000")[0];

const GoalDisplay = (props) => {
    // let endpt = "http://127.0.0.1";

    const [msg, setMsg] = useState(0);

    const goal_trigger_msg = "Instructions and Your goals (click to reopen)";

    const goal_trigger_msg_open = "(click here to collapse)";

    Axios.get(addr + ':8000/get_goal?id=' + props.uuid).then(resp => {

        setMsg(resp.data)
    });

    return (
        <div>
            <Collapsible trigger={goal_trigger_msg} triggerWhenOpen={goal_trigger_msg_open} open="true">
                <ReactMarkdown children={msg} remarkPlugins={[remarkGfm]}/>
            </Collapsible>
        </div>
    );
}

export default GoalDisplay;
