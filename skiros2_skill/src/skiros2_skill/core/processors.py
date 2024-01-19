"""
Collection of processor, defining how a skill visits its children
"""

from skiros2_common.core.abstract_skill import State


class NoProcessor():
    """
    @brief Placeholder for primitives, that have no processor
    """

    def printType(self):
        return ''

    def reset(self):
        pass

    def processChildren(self, children, visitor):
        return State.Success


class Serial():
    """
    @brief      The default processor. Process children sequentially until all
                succeed. Restarts finished (succeeded/failed) skills. Returns on
                first occurrence of a running skill.
    """

    def printType(self):
        return '->'

    def reset(self):
        pass

    def processChildren(self, children, visitor):
        for c in children:
            state = c.visit(visitor)
            if state != State.Success:
                self.stopAll(children, visitor, children.index(c)+1)
                return state
        return State.Success

    def stopAll(self, children, visitor, index):
        for c in children[index:]:
            if c.state == State.Running:
                c.visitPreempt(visitor)


class SerialStar():
    """
    @brief      Like serial, but keeps memory of which nodes previously
                succeeded and does not tick them again. The memory index is
                reset on failure, success or preemption.
    """

    def __init__(self):
        self.reset()

    def printType(self):
        return '->*'

    def reset(self):
        self.index = 0

    def processChildren(self, children, visitor):
        for i in range(self.index, len(children)):
            c = children[i]
            state = c.visit(visitor)
            if state != State.Success:
                return state
            self.index += 1
        self.index = 0
        return State.Success


class Sequential():
    """
    @brief      Alias of SerialStar. Deprecated
    """

    def __init__(self):
        self.reset()

    def printType(self):
        return '->*'

    def reset(self):
        self.index = 0

    def processChildren(self, children, visitor):
        for i in range(self.index, len(children)):
            c = children[i]
            state = c.visit(visitor)
            if state != State.Success:
                return state
            self.index += 1
        self.index = 0
        return State.Success


class Selector():
    """
    @brief      Process children in sequence until one succeeds, ignoring
                failures. Returns on first occurrence of a running or successful
                skill.
    """

    def printType(self):
        return '?'

    def reset(self):
        pass

    def processChildren(self, children, visitor):
        for c in children:
            state = c.visit(visitor)
            if state == State.Success or state == State.Running:
                self.stopAll(children, visitor, children.index(c)+1)
                return state
        return state

    def stopAll(self, children, visitor, index):
        for c in children[index:]:
            if c.state == State.Running:
                c.visitPreempt(visitor)


class SelectorStar():
    """
    @brief      Like Selector, but keeps memory of which nodes previously
                succeeded and do not tick them again. The memory index is reset
                on failure, success or preemption.
    """

    def printType(self):
        return '?*'

    def reset(self):
        self.index = 0

    def processChildren(self, children, visitor):
        for i in range(self.index, len(children)):
            c = children[i]
            state = c.visit(visitor)
            if state == State.Success or state == State.Running:
                self.stopAll(children, visitor, children.index(c)+1)
                return state
            self.index += 1
        self.index = 0
        return State.Failure

    def stopAll(self, children, visitor, index):
        for c in children[index:]:
            if c.state == State.Running:
                c.visitPreempt(visitor)


class ParallelFf():
    """
    @brief      Parallel First Fail - Process children in parallel until all
                succeed. Stop all processes if a child fails.
    """

    def printType(self):
        return '|ff|'

    def reset(self):
        pass

    def processChildren(self, children, visitor):
        state = State.Success
        for c in children:
            cstate = c.visit(visitor)
            if cstate == State.Running:
                state = State.Running
            if cstate == State.Idle and state != State.Running:
                state = State.Idle
            if cstate == State.Failure:
                self.stopAll(children, visitor)
                return State.Failure
        return state

    def stopAll(self, children, visitor):
        for c in children:
            if c.state == State.Running:
                c.visitPreempt(visitor)


class ParallelFs():
    """
    @brief      Parallel First Success - Process children in parallel until one
                succeed. Stop all processes if a child succeed/fails.
    """

    def printType(self):
        return '|fs|'

    def reset(self):
        pass

    def processChildren(self, children, visitor):
        for c in children:
            state = c.visit(visitor)
            if state != State.Running and state != State.Idle:
                self.stopAll(children, visitor)
                return state
        return State.Running

    def stopAll(self, children, visitor):
        for c in children:
            if c.state == State.Running:
                c.visitPreempt(visitor)


class NoFail():
    """
    @brief      Returns only running or success. Failure state is converted in
                Success state.
    """

    def __init__(self, processor):
        self._processor = processor

    def reset(self):
        self._processor.reset()

    def printType(self):
        return 'NoFail({})'.format(self._processor.printType())

    def processChildren(self, children, visitor):
        """
        Ignore failed execution
        """
        state = self._processor.processChildren(children, visitor)
        if state == State.Running:
            return state
        else:
            return State.Success

class RetryOnFail():
    """
    @brief Like Sequential, but retries up to max_retries if a child node fails.
           Restarts all child nodes on failure.
    """

    def __init__(self, max_retries=-1):
        self.max_retries = max_retries
        self.i = -1
        self.index = 0

    def printType(self):
        return 'RetryOnFail({})'.format(self.max_retries)

    def reset(self):
        self.i = -1
        self.index = 0

    def processChildren(self, children, visitor):
        
        for i in range(self.index, len(children)):
            c = children[i]
            state = c.visit(visitor)
            if state == State.Failure:
                self.index = 0
                self.i += 1
                if self.i == self.max_retries:
                    return State.Failure
                else:
                    return State.Running
            elif state != State.Success:
                return state
            self.index += 1

        return State.Success
